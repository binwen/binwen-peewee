import json
import datetime
import peewee
import pendulum


peewee.MySQLDatabase.field_types.update({'DATETIME': 'DATETIME(6)'})
peewee.PostgresqlDatabase.field_types.update({'DATETIME': 'TIMESTAMPTZ'})
__all__ = [
    "DatetimeTZField",
    "JSONTextField",
    "CreationDateTimeField",
    "ModificationDateTimeField"
]


class DatetimeTZField(peewee.Field):
    field_type = 'DATETIME'

    def __init__(self, tz="Asia/Shanghai", *args, **kwargs):
        self.tz = tz
        super().__init__(*args, **kwargs)

    def python_value(self, value):
        if isinstance(value, str):
            return pendulum.parse(value)
        if isinstance(value, datetime.datetime):
            return pendulum.instance(value)
        return value

    def db_value(self, value):
        if value is None:
            return value

        if isinstance(value, str):
            value = pendulum.parse(value, tz=self.tz)

        if not isinstance(value, datetime.datetime):
            raise ValueError('datetime instance required')
        if value.utcoffset() is None:
            raise ValueError('timezone aware datetime required')
        if isinstance(value, pendulum.DateTime):
            value = datetime.datetime.fromtimestamp(value.timestamp(), tz=value.timezone)
        return value.astimezone(datetime.timezone.utc)


class JSONTextField(peewee.TextField):
    field_type = 'JSON'

    def db_value(self, value):
        if value is None:
            return value
        data = json.dumps(value)
        return data

    def python_value(self, value):
        if value is None:
            return value
        return json.loads(value)


class CreationDateTimeField(DatetimeTZField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get("default", None):
            kwargs["default"] = pendulum.now

        super().__init__(*args, **kwargs)


class ModificationDateTimeField(DatetimeTZField):
    def __init__(self, auto_now=True, *args, **kwargs):
        if auto_now:
            kwargs["default"] = pendulum.now
        else:
            kwargs["null"] = True
        self.update_modified = True
        super().__init__(*args, **kwargs)
