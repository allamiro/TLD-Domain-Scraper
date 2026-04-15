import csv
import io
import logging

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from selenium.common.exceptions import WebDriverException

from app.models import Domain
from app.scraper import run_scraper

bp = Blueprint("main", __name__)
log = logging.getLogger(__name__)

RESULTS_PER_PAGE = 50


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/scrape", methods=["GET", "POST"])
def scrape():
    if request.method == "POST":
        raw = request.form.get("tlds", "").strip()
        if not raw:
            flash("Please enter at least one TLD.", "warning")
            return redirect(url_for("main.scrape"))

        tlds = [t.strip() for t in raw.split(",") if t.strip()]
        try:
            count = run_scraper(tlds)
            flash(f"Scraping complete. {count} new domain(s) added.", "success")
        except WebDriverException as e:
            log.error(f"Scraper failed: {e}")
            flash(
                "Scraping failed — Chrome/WebDriver error. Check server logs.",
                "danger",
            )
        except Exception as e:
            log.error(f"Unexpected scraper error: {e}")
            flash("An unexpected error occurred during scraping.", "danger")

        return redirect(url_for("main.results"))

    return render_template("scrape.html")


@bp.route("/results")
def results():
    page = request.args.get("page", 1, type=int)
    tld_filter = request.args.get("tld", "").strip()
    search_query = request.args.get("q", "").strip()

    query = Domain.query

    if tld_filter:
        query = query.filter(Domain.tld.ilike(f"%{tld_filter}%"))
    if search_query:
        query = query.filter(Domain.url.ilike(f"%{search_query}%"))

    query = query.order_by(Domain.timestamp.desc())
    pagination = query.paginate(page=page, per_page=RESULTS_PER_PAGE, error_out=False)

    # Distinct TLD list for the filter dropdown
    tld_list = [row.tld for row in Domain.query.with_entities(Domain.tld).distinct().all()]

    return render_template(
        "results.html",
        domains=pagination.items,
        pagination=pagination,
        tld_list=sorted(tld_list),
        tld_filter=tld_filter,
        search_query=search_query,
    )


@bp.route("/download")
def download():
    tld_filter = request.args.get("tld", "").strip()
    query = Domain.query
    if tld_filter:
        query = query.filter(Domain.tld.ilike(f"%{tld_filter}%"))

    domains = query.order_by(Domain.tld, Domain.url).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "url", "tld", "timestamp"])
    for d in domains:
        writer.writerow([d.id, d.url, d.tld, d.timestamp.isoformat()])
    output.seek(0)

    filename = f"domains{'_' + tld_filter if tld_filter else ''}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )
