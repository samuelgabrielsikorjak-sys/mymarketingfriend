from database import init_db, get_db
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

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
    
    


        