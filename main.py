from database import init_db, get_db
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from ai import score_lead, generate_copy

templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan= lifespan)
app.mount("/static", StaticFiles(directory="static"), name = "static")

@app.get("/")
def home():
    return templates.TemplateResponse("/")

@app.get("/leads")
def leads(request: Request):
    conn = get_db()
    leads_rows = conn.execute("SELECT * FROM leads").fetchall()
    return templates.TemplateResponse(request, "leads.html", {"leads": leads_rows})

@app.get("/leads/new")
def new_lead_form(request: Request):
    return templates.TemplateResponse(request, "new_lead.html", {})

@app.post("/leads/new")
def new_lead_save(name: str = Form(...), company: str = Form(...), web_site_url: str = Form(...), sector: str = Form(...), notes: str = Form()):
    conn = get_db()
    conn.execute("INSERT INTO leads(name, company, web_site_url, sector, notes ) VALUES (?, ?, ?, ?, ?)", (name, company, web_site_url, sector, notes))
    conn.commit()
    return RedirectResponse(url="/leads", status_code = 303)

@app.get("/leads/{id}")
def lead_detail(id: int, request: Request):
    conn = get_db()
    lead = conn.execute("SELECT * FROM leads WHERE id = ?", (id,)).fetchone()
    return templates.TemplateResponse(request, "lead_detail.html", {"lead": lead})

@app.get("/leads/{id}/edit")
def edit_lead(id: int, request: Request):
    conn = get_db()
    lead = conn.execute("SELECT * FROM leads WHERE id = ?",(id,)).fetchone()
    return templates.TemplateResponse(request, "edit_lead.html",{"lead": lead})

@app.post("/leads/{id}/edit")
def update_lead(id: int, name: str = Form(...), company: str = Form(...), web_site_url: str = Form(...), sector: str = Form(...), notes: str = Form()):
    conn = get_db()
    conn.execute("UPDATE leads SET name = ?, company = ?, web_site_url = ?, sector = ?, notes = ? WHERE id = ?", (name, company, web_site_url, sector, notes, id))
    conn.commit()
    return RedirectResponse(url="/leads", status_code = 303)

@app.post("/leads/{id}/delete")
def delete_lead(id: int, request: Request):
    conn = get_db()
    conn.execute("DELETE FROM leads WHERE id = ?", (id,))
    conn.commit()
    return RedirectResponse(url="/leads", status_code = 303)

@app.get("/settings")
def settings(request: Request):
    conn = get_db()
    icp =conn.execute("SELECT icp_desc FROM settings").fetchone()
    return templates.TemplateResponse(request,"settings.html",{"icp": icp})

@app.post("/settings")
def get_new_icp(icp_desc: str = Form(...)):
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
        score, score_reasoning = score_lead(lead["name"], lead["company"], lead["sector"], lead["notes"])
        conn.execute("UPDATE leads SET score = ?, score_reasoning = ? WHERE id = ?", (score, score_reasoning, lead["id"]))
    conn.commit()
    return RedirectResponse(url="/leads", status_code=303)

@app.post("/leads/{id}/generate")
def generate_mail_route(request: Request, id: int):
    conn = get_db()
    lead = conn.execute("SELECT * FROM leads WHERE id = ?",(id,)).fetchone()
    copy_1, copy_2 = generate_copy(lead["name"], lead["company"], lead["sector"], lead["notes"], lead["score_reasoning"], lead["web_site_url"])
    return templates.TemplateResponse(request,"lead_detail.html",{"lead": lead, "script_1": copy_1, "script_2": copy_2})
    

@app.post("/leads/{id}/save_email")
def save_mail_db(id: int, chosen_name: str = Form(...), chosen_email: str = Form(...)):
    conn = get_db()
    conn.execute("UPDATE leads SET mail = ?, chosen_script = ? WHERE id = ?", (chosen_email, chosen_name, id))
    conn.commit()
    return RedirectResponse(url=f"/leads/{id}", status_code=303)