from __future__ import annotations

import csv
import io
import logging
import threading

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from selenium.common.exceptions import WebDriverException

from app.models import Domain
from app.scraper import run_scraper
from app import jobs as job_store

bp = Blueprint("main", __name__)
log = logging.getLogger(__name__)

RESULTS_PER_PAGE = 50


@bp.route("/")
def index():
    return render_template("index.html")


# ── Scrape ──────────────────────────────────────────────────────────────────

@bp.route("/scrape", methods=["GET", "POST"])
def scrape():
    if request.method == "POST":
        raw = request.form.get("tlds", "").strip()
        if not raw:
            flash("Please enter at least one TLD.", "warning")
            return redirect(url_for("main.scrape"))

        tlds = [t.strip() for t in raw.split(",") if t.strip()]
        job_id = job_store.create_job(tlds)

        # Run the scraper in a background thread so the request returns immediately
        app = current_app._get_current_object()

        def _run():
            job_store.start_job(job_id)
            with app.app_context():
                try:
                    inserted = run_scraper(tlds, job_id=job_id)
                    job_store.finish_job(job_id, inserted)
                except WebDriverException as e:
                    job_store.fail_job(job_id, str(e.msg if hasattr(e, "msg") else e))
                except Exception as e:
                    job_store.fail_job(job_id, str(e))

        threading.Thread(target=_run, daemon=True).start()
        return redirect(url_for("main.progress", job_id=job_id))

    return render_template("scrape.html")


# ── Progress & status ────────────────────────────────────────────────────────

@bp.route("/progress/<job_id>")
def progress(job_id):
    job = job_store.get_job(job_id)
    if not job:
        flash("Job not found.", "warning")
        return redirect(url_for("main.scrape"))
    return render_template("progress.html", job=job)


@bp.route("/status/<job_id>")
def status(job_id):
    """JSON endpoint polled by the progress page."""
    job = job_store.get_job(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    return jsonify(job)


# ── Results ──────────────────────────────────────────────────────────────────

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

    tld_list = [
        row.tld
        for row in Domain.query.with_entities(Domain.tld).distinct().all()
    ]

    return render_template(
        "results.html",
        domains=pagination.items,
        pagination=pagination,
        tld_list=sorted(tld_list),
        tld_filter=tld_filter,
        search_query=search_query,
    )


# ── Download ─────────────────────────────────────────────────────────────────

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
