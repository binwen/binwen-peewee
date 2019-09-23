import grpc
from playhouse import db_url
from peewee import DoesNotExist, DataError
from binwen.pb2 import default_pb2
from binwen.utils.cache import cached_property
from binwen.middleware import MiddlewareMixin


from peeweext.exceptions import ValidationError
from peeweext.models import TimeStampedModel, Model


class PeeweeExt:
    def __init__(self, alias='default'):
        self.alias = alias
        self.database = None

    def init_app(self, app):
        db_config = app.config["DATABASES"][self.alias]
        conn_params = db_config.get('CONN_OPTIONS', {})
        self.database = db_url.connect(db_config['DB_URL'], **conn_params)
        self.try_setup_celery()

    @cached_property
    def Model(self):
        class BaseModel(Model):
            class Meta:
                database = self.database

        return BaseModel

    @cached_property
    def TimeStampedModel(self):
        class BaseTimeStampedModel(TimeStampedModel):
            class Meta:
                database = self.database

        return BaseTimeStampedModel

    def connect_db(self):
        if self.database.is_closed():
            self.database.connect()

    def close_db(self):
        if not self.database.is_closed():
            self.database.close()

    def try_setup_celery(self):
        try:
            from celery.signals import task_prerun, task_postrun
            task_prerun.connect(lambda *arg, **kw: self.connect_db(), weak=False)
            task_postrun.connect(lambda *arg, **kw: self.close_db(), weak=False)
        except ImportError:
            pass


class PeeweeExtMiddleware(MiddlewareMixin):
    def __init__(self, app, handler, origin_handler):
        super().__init__(app, handler, origin_handler)
        self.peewee_exts = [ext for ext in app.extensions.values() if isinstance(ext, PeeweeExt)]

    def connect_db(self):
        for pwx in self.peewee_exts:
            pwx.connect_db()

    def close_db(self):
        for pwx in self.peewee_exts:
            pwx.close_db()

    def __call__(self, servicer, request, context):
        try:
            self.connect_db()
            return self.handler(servicer, request, context)
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Record Not Found')
        except (ValidationError, DataError) as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
        finally:
            self.close_db()
        return default_pb2.Empty()

