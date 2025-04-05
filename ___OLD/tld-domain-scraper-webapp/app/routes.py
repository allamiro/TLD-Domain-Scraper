from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file
from app.models import Domain
from app.scraper import run_scraper

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if request.method == 'POST':
        tlds = request.form.get('tlds', '').split(',')
        run_scraper([tld.strip() for tld in tlds])
        return redirect(url_for('main.results'))
    return render_template('scrape.html')

@bp.route('/results')
def results():
    domains = Domain.query.all()
    return render_template('results.html', domains=domains)

@bp.route('/download')
def download():
    # Same logic for downloading CSV
    pass
