from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List
import os
from sqlalchemy.sql import func

from .models import Domain, get_db
from .services.scraper import DomainScraper

app = FastAPI(title="TLD Domain Scraper")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    """Render the home page with the scraping form and dashboard"""
    # Get recent domains for the dashboard
    recent_domains = db.query(Domain).order_by(Domain.created_at.desc()).limit(10).all()
    tld_stats = db.query(Domain.tld, func.count(Domain.id)).group_by(Domain.tld).all()
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "TLD Domain Scraper",
            "recent_domains": recent_domains,
            "tld_stats": tld_stats
        }
    )

@app.post("/scrape")
async def scrape_domains(
    tld: str = Form(...),
    db: Session = Depends(get_db)
):
    """Trigger domain scraping for a specific TLD"""
    try:
        scraper = DomainScraper()
        domains = await scraper.scrape_tld(tld)
        
        # Store domains in database
        for domain in domains:
            db_domain = Domain(domain_name=domain, tld=tld)
            db.add(db_domain)
        
        db.commit()
        return RedirectResponse(url="/", status_code=303)
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

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get scraping statistics"""
    total_domains = db.query(Domain).count()
    tld_stats = db.query(Domain.tld, func.count(Domain.id)).group_by(Domain.tld).all()
    recent_domains = db.query(Domain).order_by(Domain.created_at.desc()).limit(10).all()
    
    return {
        "total_domains": total_domains,
        "tld_stats": dict(tld_stats),
        "recent_domains": [
            {
                "domain_name": domain.domain_name,
                "tld": domain.tld,
                "created_at": domain.created_at
            }
            for domain in recent_domains
        ]
    } 