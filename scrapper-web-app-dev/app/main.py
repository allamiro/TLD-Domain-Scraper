from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import os

from .models import Domain, get_db
from .services.scraper import DomainScraper

app = FastAPI(title="TLD Domain Scraper")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    """Render the home page with the scraping form"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "TLD Domain Scraper"}
    )

@app.post("/scrape")
async def scrape_domains(tld: str, db: Session = Depends(get_db)):
    """Trigger domain scraping for a specific TLD"""
    try:
        scraper = DomainScraper()
        domains = await scraper.scrape_tld(tld)
        
        # Store domains in database
        for domain in domains:
            db_domain = Domain(domain_name=domain, tld=tld)
            db.add(db_domain)
        
        db.commit()
        return {"message": f"Successfully scraped {len(domains)} domains for {tld}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/domains")
async def list_domains(db: Session = Depends(get_db)):
    """List all stored domains"""
    domains = db.query(Domain).all()
    return [
        {
            "id": domain.id,
            "domain_name": domain.domain_name,
            "tld": domain.tld,
            "created_at": domain.created_at
        }
        for domain in domains
    ]

@app.get("/domains/{tld}")
async def list_domains_by_tld(tld: str, db: Session = Depends(get_db)):
    """List domains for a specific TLD"""
    domains = db.query(Domain).filter(Domain.tld == tld).all()
    return [
        {
            "id": domain.id,
            "domain_name": domain.domain_name,
            "tld": domain.tld,
            "created_at": domain.created_at
        }
        for domain in domains
    ] 