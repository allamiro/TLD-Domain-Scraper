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

from app.models import Domain, ScrapeRun
from app.scraper import run_scraper
from app import jobs as job_store
from app.engines import ALL_ENGINES, DEFAULT_ENGINES

bp = Blueprint("main", __name__)
log = logging.getLogger(__name__)

RESULTS_PER_PAGE = 50


@bp.route("/")
def index():
    total_domains = Domain.query.count()
    total_runs    = ScrapeRun.query.count()
    recent_runs   = (ScrapeRun.query
                     .order_by(ScrapeRun.started_at.desc())
                     .limit(5).all())
    return render_template("index.html",
                           total_domains=total_domains,
                           total_runs=total_runs,
                           recent_runs=recent_runs)


# ── Scrape ───────────────────────────────────────────────────────────────────

@bp.route("/scrape", methods=["GET", "POST"])
def scrape():
    if request.method == "POST":
        raw  = request.form.get("tlds", "").strip()
        mode = request.form.get("mode", "append")
        if mode not in ("append", "replace"):
            mode = "append"

        # Multi-select checkboxes — getlist returns [] if none checked
        engine_keys = request.form.getlist("engines")
        if not engine_keys:
            engine_keys = DEFAULT_ENGINES

        if not raw:
            flash("Please enter at least one TLD.", "warning")
            return redirect(url_for("main.scrape"))

        tlds = [t.strip() for t in raw.split(",") if t.strip()]
        job_id = job_store.create_job(tlds)

        app = current_app._get_current_object()

        def _run():
            job_store.start_job(job_id)
            with app.app_context():
                try:
                    inserted = run_scraper(tlds, job_id=job_id, mode=mode, engine_keys=engine_keys)
                    job_store.finish_job(job_id, inserted)
                except WebDriverException as e:
                    job_store.fail_job(job_id, str(e.msg if hasattr(e, "msg") else e))
                except Exception as e:
                    job_store.fail_job(job_id, str(e))

        threading.Thread(target=_run, daemon=True).start()
        return redirect(url_for("main.progress", job_id=job_id))

    return render_template("scrape.html", all_engines=ALL_ENGINES, default_engines=DEFAULT_ENGINES)


# ── Progress & status ─────────────────────────────────────────────────────────

@bp.route("/progress/<job_id>")
def progress(job_id):
    job = job_store.get_job(job_id)
    if not job:
        flash("Job not found.", "warning")
        return redirect(url_for("main.scrape"))
    return render_template("progress.html", job=job)


@bp.route("/status/<job_id>")
def status(job_id):
    job = job_store.get_job(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    return jsonify(job)


# ── Run history ───────────────────────────────────────────────────────────────

@bp.route("/history")
def history():
    page = request.args.get("page", 1, type=int)
    tld_filter = request.args.get("tld", "").strip()

    query = ScrapeRun.query
    if tld_filter:
        query = query.filter(ScrapeRun.tld.ilike(f"%{tld_filter}%"))
    query = query.order_by(ScrapeRun.started_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)

    tld_list = [r.tld for r in ScrapeRun.query.with_entities(ScrapeRun.tld).distinct().all()]

    return render_template(
        "history.html",
        runs=pagination.items,
        pagination=pagination,
        tld_list=sorted(tld_list),
        tld_filter=tld_filter,
    )


@bp.route("/history/<int:run_id>")
def run_detail(run_id):
    run = ScrapeRun.query.get_or_404(run_id)
    page = request.args.get("page", 1, type=int)
    pagination = (Domain.query
                  .filter_by(run_id=run_id)
                  .order_by(Domain.url)
                  .paginate(page=page, per_page=RESULTS_PER_PAGE, error_out=False))
    return render_template("run_detail.html", run=run, pagination=pagination)


# ── Results ───────────────────────────────────────────────────────────────────

@bp.route("/results")
def results():
    page         = request.args.get("page", 1, type=int)
    tld_filter   = request.args.get("tld", "").strip()
    search_query = request.args.get("q", "").strip()

    query = Domain.query
    if tld_filter:
        query = query.filter(Domain.tld.ilike(f"%{tld_filter}%"))
    if search_query:
        query = query.filter(Domain.url.ilike(f"%{search_query}%"))
    query = query.order_by(Domain.discovered_at.desc())
    pagination = query.paginate(page=page, per_page=RESULTS_PER_PAGE, error_out=False)

    tld_list = [r.tld for r in Domain.query.with_entities(Domain.tld).distinct().all()]

    return render_template(
        "results.html",
        domains=pagination.items,
        pagination=pagination,
        tld_list=sorted(tld_list),
        tld_filter=tld_filter,
        search_query=search_query,
    )


# ── Download ──────────────────────────────────────────────────────────────────

@bp.route("/download")
def download():
    tld_filter = request.args.get("tld", "").strip()
    run_id     = request.args.get("run_id", type=int)

    query = Domain.query
    if run_id:
        query = query.filter_by(run_id=run_id)
    elif tld_filter:
        query = query.filter(Domain.tld.ilike(f"%{tld_filter}%"))
    domains = query.order_by(Domain.tld, Domain.url).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "url", "tld", "run_id", "discovered_at"])
    for d in domains:
        writer.writerow([d.id, d.url, d.tld, d.run_id,
                         d.discovered_at.isoformat() if d.discovered_at else ""])
    output.seek(0)

    if run_id:
        fname = f"domains_run{run_id}.csv"
    elif tld_filter:
        fname = f"domains_{tld_filter}.csv"
    else:
        fname = "domains_all.csv"

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=fname,
    )
