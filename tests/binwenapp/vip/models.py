import peeweext
from extensions import db


class Note(db.Model):
    message = peeweext.TextField()
    published_at = peeweext.DatetimeTZField(null=True)
    detail = peeweext.JSONTextField()
