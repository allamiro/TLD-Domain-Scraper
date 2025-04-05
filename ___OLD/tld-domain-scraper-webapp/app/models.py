from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Domain(db.Model):
    __tablename__ = 'domains'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    tld = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
