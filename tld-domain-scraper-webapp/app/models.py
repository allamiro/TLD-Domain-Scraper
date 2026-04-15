from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ScrapeRun(db.Model):
    """One row per scrape job/TLD combination — the 'run' that found the domains."""
    __tablename__ = "scrape_runs"

    id         = db.Column(db.Integer, primary_key=True)
    job_id     = db.Column(db.String(64), nullable=False, index=True)
    tld        = db.Column(db.String(64), nullable=False)
    mode       = db.Column(db.String(16), nullable=False, default="append")
    engines    = db.Column(db.String(128), nullable=True)   # comma-separated engine keys
    # append = keep old rows + insert new ones
    # replace = delete all existing rows for this TLD before inserting

    started_at  = db.Column(db.DateTime, nullable=False,
                            default=lambda: datetime.now(timezone.utc))
    finished_at = db.Column(db.DateTime, nullable=True)
    domains_found    = db.Column(db.Integer, nullable=False, default=0)
    domains_inserted = db.Column(db.Integer, nullable=False, default=0)
    domains_deleted  = db.Column(db.Integer, nullable=False, default=0)

    domains = db.relationship("Domain", back_populates="run",
                              cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self):
        return f"<ScrapeRun id={self.id} tld={self.tld} job={self.job_id}>"


class Domain(db.Model):
    __tablename__ = "domains"

    id     = db.Column(db.Integer, primary_key=True)
    url    = db.Column(db.String(512), nullable=False)
    tld    = db.Column(db.String(64),  nullable=False)
    run_id = db.Column(db.Integer, db.ForeignKey("scrape_runs.id", ondelete="CASCADE"),
                       nullable=True)
    discovered_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    run = db.relationship("ScrapeRun", back_populates="domains")

    # A URL should be unique within a single TLD (across all runs)
    __table_args__ = (
        db.UniqueConstraint("url", "tld", name="uq_domain_url_tld"),
    )

    def __repr__(self):
        return f"<Domain id={self.id} url={self.url} tld={self.tld}>"
