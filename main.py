import re
from database import init_db, get_db
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from ai import score_lead, generate_copy
from fastapi import HTTPException

templates = Jinja2Templates(directory="templates")

MAX_SHORT_FIELD_LEN = 200
MAX_NOTES_LEN = 5000
URL_PATTERN = re.compile(r"^[\w\-]+(\.[\w\-]+)+")


def validate_lead_fields(name: str, company: str, web_site_url: str, sector: str, status: str, contact: str, notes: str):
    name = name.strip()
    company = company.strip()
    web_site_url = web_site_url.strip()
    sector = sector.strip()
    status = status.strip()
    contact = contact.strip()
    notes = notes.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if len(name) > MAX_SHORT_FIELD_LEN:
        raise HTTPException(status_code=400, detail="Name is too long")
    if not company:
        raise HTTPException(status_code=400, detail="Company is required")
    if len(company) > MAX_SHORT_FIELD_LEN:
        raise HTTPException(status_code=400, detail="Company is too long")
    if not web_site_url:
        raise HTTPException(status_code=400, detail="Website URL is required")
    if len(web_site_url) > MAX_SHORT_FIELD_LEN or not URL_PATTERN.match(web_site_url):
        raise HTTPException(status_code=400, detail="Website URL is invalid")
    if not sector:
        raise HTTPException(status_code=400, detail="Sector is required")
    if len(sector) > MAX_SHORT_FIELD_LEN:
        raise HTTPException(status_code=400, detail="Sector is too long")
    if not status:
        raise HTTPException(status_code=400, detail="No Status")
    if not contact:
        raise HTTPException(status_code=400, detail="No Contact")
    if len(notes) > MAX_NOTES_LEN:
        raise HTTPException(status_code=400, detail="Notes are too long")

    return name, company, web_site_url, sector, status, contact, notes

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan= lifespan)
app.mount("/static", StaticFiles(directory="static"), name = "static")

@app.get("/")
def home(request:Request):
    return templates.TemplateResponse(request,"home.html")

@app.get("/leads")
def leads(request: Request):
    conn = get_db()
    leads_rows = conn.execute("SELECT * FROM leads").fetchall()
    return templates.TemplateResponse(request, "leads.html", {"leads": leads_rows})

@app.get("/leads/new")
def new_lead_form(request: Request):
    return templates.TemplateResponse(request, "new_lead.html", {})

@app.post("/leads/new")
def new_lead_save(name: str = Form(...), company: str = Form(...), web_site_url: str = Form(...), sector: str = Form(...), status: str = Form(...), contact: str = Form(...), notes: str = Form()):
    name, company, web_site_url, sector, status, contact, notes = validate_lead_fields(name, company, web_site_url, sector, status, contact, notes)
    conn = get_db()
    conn.execute("INSERT INTO leads(name, company, web_site_url, sector, status, contact, notes ) VALUES (?, ?, ?, ?, ?, ?, ?)", (name, company, web_site_url, sector, status, contact, notes))
    conn.commit()
    return RedirectResponse(url="/leads", status_code = 303)

@app.get("/leads/{id}")
def lead_detail(id: int, request: Request):
    conn = get_db()
    lead = conn.execute("SELECT * FROM leads WHERE id = ?", (id,)).fetchone()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return templates.TemplateResponse(request, "lead_detail.html", {"lead": lead})

@app.get("/leads/{id}/edit")
def edit_lead(id: int, request: Request):
    conn = get_db()
    lead = conn.execute("SELECT * FROM leads WHERE id = ?",(id,)).fetchone()
    if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
    return templates.TemplateResponse(request, "edit_lead.html",{"lead": lead})

@app.post("/leads/{id}/edit")
def update_lead(id: int, name: str = Form(...), company: str = Form(...), web_site_url: str = Form(...), sector: str = Form(...), status: str = Form(...), contact: str = Form(...), notes: str = Form()):
    name, company, web_site_url, sector, status, contact, notes = validate_lead_fields(name, company, web_site_url, sector, status, contact, notes)
    conn = get_db()
    rows = conn.execute("UPDATE leads SET name = ?, company = ?, web_site_url = ?, sector = ?, status = ?, contact = ?, notes = ? WHERE id = ?", (name, company, web_site_url, sector, status, contact, notes, id))
    if rows.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
    conn.commit()
    return RedirectResponse(url="/leads", status_code = 303)

@app.post("/leads/{id}/delete")
def delete_lead(id: int, request: Request):
    conn = get_db()
    rows = conn.execute("DELETE FROM leads WHERE id = ?", (id,))
    if rows.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
    conn.commit()
    return RedirectResponse(url="/leads", status_code = 303)

@app.get("/settings")
def settings(request: Request):
    conn = get_db()
    icp =conn.execute("SELECT icp_desc FROM settings").fetchone()
    return templates.TemplateResponse(request,"settings.html",{"icp": icp})

@app.post("/settings")
def get_new_icp(icp_desc: str = Form(...)):
    icp_desc = icp_desc.strip()
    if not icp_desc:
        raise HTTPException(status_code=400, detail="ICP description is required")
    if len(icp_desc) > MAX_NOTES_LEN:
        raise HTTPException(status_code=400, detail="ICP description is too long")
    conn = get_db()
    existing = conn.execute("SELECT * FROM settings").fetchone()
    if not existing:
        conn.execute("INSERT INTO settings(icp_desc) VALUES(?)",(icp_desc,))
    else:
        conn.execute("UPDATE settings SET icp_desc = ? WHERE id = ?", (icp_desc, existing["id"]))
    conn.commit()
    return RedirectResponse(url = "/settings", status_code = 303)

@app.post("/leads/evaluate")
def evaluate_all():
    conn = get_db()
    unscored = conn.execute("SELECT * FROM leads WHERE score IS NULL").fetchall()
    for lead in unscored:
        try:
            score, score_reasoning = score_lead(lead["name"], lead["company"], lead["sector"], lead["notes"])
            conn.execute("UPDATE leads SET score = ?, score_reasoning = ? WHERE id = ?", (score, score_reasoning, lead["id"]))
        except Exception:
            continue
    conn.commit()
    return RedirectResponse(url="/leads", status_code=303)

@app.post("/leads/{id}/generate")
def generate_mail_route(request: Request, id: int):
    conn = get_db()
    lead = conn.execute("SELECT * FROM leads WHERE id = ?",(id,)).fetchone()
    if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
    try:
        copy_1, copy_2 = generate_copy(lead["name"], lead["company"], lead["sector"], lead["notes"], lead["score_reasoning"], lead["web_site_url"])
    except Exception as e:
        raise HTTPException(status_code=502, detail="Failed to generate email copy") from e
    return templates.TemplateResponse(request,"lead_detail.html",{"lead": lead, "script_1": copy_1, "script_2": copy_2})
    

@app.post("/leads/{id}/save_email")
def save_mail_db(id: int, chosen_name: str = Form(...), chosen_email: str = Form(...)):
    chosen_name = chosen_name.strip()
    chosen_email = chosen_email.strip()
    if not chosen_name or not chosen_email:
        raise HTTPException(status_code=400, detail="Chosen email is required")
    conn = get_db()
    rows = conn.execute("UPDATE leads SET mail = ?, chosen_script = ? WHERE id = ?", (chosen_email, chosen_name, id))
    if rows.rowcount == 0:
                raise HTTPException(status_code=404, detail="Lead not found")
    conn.commit()
    return RedirectResponse(url=f"/leads/{id}", status_code=303)