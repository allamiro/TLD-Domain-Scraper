from fastapi import FastAPI, Request, Depends, HTTPException, Form, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict
import os
from sqlalchemy.sql import func
import logging
import json
from datetime import datetime

from .models import Domain, get_db
from .services.scraper import DomainScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TLD Domain Scraper")

# Store active scraping tasks
active_scrapers: Dict[str, DomainScraper] = {}

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

@app.websocket("/ws/{tld}")
async def websocket_endpoint(websocket: WebSocket, tld: str):
    """WebSocket endpoint for real-time scraping updates"""
    await websocket.accept()
    try:
        scraper = DomainScraper(websocket)
        active_scrapers[tld] = scraper
        domains = await scraper.scrape_tld(tld)
        
        # Store domains in database
        db = next(get_db())
        for domain in domains:
            db_domain = Domain(domain_name=domain, tld=tld)
            db.add(db_domain)
        db.commit()
        
        await websocket.send_json({
            "type": "complete",
            "message": f"Scraping completed. Found {len(domains)} domains.",
            "domains": list(domains)
        })
    except WebSocketDisconnect:
        if tld in active_scrapers:
            active_scrapers[tld].cancel()
            del active_scrapers[tld]
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()

@app.post("/scrape")
async def scrape_domains(
    request: Request,
    tld: str = Form(...),
    db: Session = Depends(get_db)
):
    """Trigger domain scraping for a specific TLD"""
    if tld in active_scrapers:
        raise HTTPException(status_code=400, detail="Scraping already in progress for this TLD")
    
    return templates.TemplateResponse(
        "scraping.html",
        {
            "request": request,
            "tld": tld,
            "ws_url": f"/ws/{tld}"
        }
    )

@app.post("/cancel/{tld}")
async def cancel_scraping(tld: str):
    """Cancel an ongoing scraping operation"""
    if tld in active_scrapers:
        active_scrapers[tld].cancel()
        del active_scrapers[tld]
        return {"message": "Scraping cancelled"}
    raise HTTPException(status_code=404, detail="No active scraping found for this TLD")

@app.get("/download/{tld}")
async def download_domains(tld: str, db: Session = Depends(get_db)):
    """Download domains for a specific TLD as a text file"""
    domains = db.query(Domain).filter(Domain.tld == tld).all()
    if not domains:
        raise HTTPException(status_code=404, detail="No domains found for this TLD")
    
    # Create temporary file
    filename = f"domains_{tld.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = f"app/static/downloads/{filename}"
    os.makedirs("app/static/downloads", exist_ok=True)
    
    with open(filepath, "w") as f:
        for domain in domains:
            f.write(f"{domain.domain_name}\n")
    
    return FileResponse(
        filepath,
        media_type="text/plain",
        filename=filename,
        background=None
    )

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