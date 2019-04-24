import peewee
from peeweext import fields

from extensions import db


class Note(db.Model):
    message = peewee.TextField()
    published_at = fields.DatetimeTZField(null=True)
    detail = fields.JSONField()
