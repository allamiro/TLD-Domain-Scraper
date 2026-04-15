import os
from flask import Flask
from app.models import db


def create_app():
    app = Flask(__name__)

    # Prefer the DATABASE_URL env var (set by docker-compose / production).
    # Fall back to a local SQLite DB for running outside Docker.
    db_uri = os.environ.get(
        "DATABASE_URL",
        "sqlite:///domains.db",
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Keep a secret key; override via SECRET_KEY env var in production
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Register the main blueprint here so create_app() is self-contained
    from app.routes import bp  # noqa: PLC0415
    app.register_blueprint(bp)

    return app
