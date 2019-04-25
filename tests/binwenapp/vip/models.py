
from extensions import db


class Note(db.Model):
    message = db.TextField()
    published_at = db.DatetimeTZField(null=True)
    detail = db.JSONTextField()
