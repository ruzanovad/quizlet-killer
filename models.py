from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)  # Поддержка HTML
    answer = db.Column(db.Text, nullable=False)    # Поддержка HTML
    card_type = db.Column(db.String(50))
    tags = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc)) # по UTC
    last_reviewed = db.Column(db.DateTime)
    next_review = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    review_count = db.Column(db.Integer, default=0)
    easiness_factor = db.Column(db.Float, default=2.5)
    interval = db.Column(db.Integer, default=1)
