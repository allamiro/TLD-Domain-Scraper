from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Domain(db.Model):
    __tablename__ = "domains"

    id = db.Column(db.Integer, primary_key=True)
    # url is the scheme://netloc base domain — must be unique per tld
    url = db.Column(db.String(512), nullable=False)
    # TLD can be a compound like .PERSIANBLOG.IR (up to 64 chars is safe)
    tld = db.Column(db.String(64), nullable=False)
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("url", "tld", name="uq_domain_url_tld"),
    )

    def __repr__(self):
        return f"<Domain id={self.id} url={self.url} tld={self.tld}>"
