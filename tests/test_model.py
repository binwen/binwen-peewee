import pytest
import peewee
import pendulum
import datetime
from io import StringIO
import inspect
import peeweext
from peeweext import signal
from peeweext.binwen import PeeweeExt
from peeweext.exceptions import ValidationError


class App:
    config = dict(DATABASES={"default": {"DB_URL": "sqlite:///:memory:"}})


app = App()
db = PeeweeExt()
db.init_app(app)


class Note(db.Model):
    message = peeweext.TextField()
    published_at = peeweext.DatetimeTZField(null=True)
    content = peeweext.JSONTextField(default={})
    remark = peeweext.JSONTextField(null=True)

    def validate_message(self, value):
        if value == 'raise error':
            raise ValidationError


class TimeStampedNote(db.TimeStampedModel):
    message = peeweext.TextField()
    published_at = peeweext.DatetimeTZField(null=True)

    def validate_message(self, value):
        if value == 'raise error':
            raise ValidationError


class WhiteListNote(db.Model):
    f1 = peeweext.IntegerField(default=1)
    f2 = peeweext.IntegerField(default=2)
    f3 = peeweext.IntegerField(default=3)
    f4 = peeweext.IntegerField(default=4)

    class Meta:
        has_whitelist = True
        accessible_fields = ['f1', 'f2', 'f3']
        protected_fields = ['f3', 'f4']


class NoWhiteListNote(db.Model):
    f1 = peeweext.IntegerField(default=1)
    f2 = peeweext.IntegerField(default=2)
    f3 = peeweext.IntegerField(default=3)
    f4 = peeweext.IntegerField(default=4)

    class Meta:
        accessible_fields = ['f1', 'f2', 'f3']
        protected_fields = ['f3', 'f4']


@pytest.fixture
def table():
    Note.create_table()
    TimeStampedNote.create_table()
    yield
    Note.drop_table()
    TimeStampedNote.drop_table()


def test_model(table):
    n = Note.create(message='Hello')
    n = Note.get(id=n.id)

    with pytest.raises(ValueError):
        n.published_at = datetime.datetime.utcnow()
        n.save()

    n.published_at = pendulum.now()
    n.save()

    out = StringIO()

    def post_delete(sender, instance):
        out.write('post_delete received')

    signal.post_delete.connect(post_delete, sender=Note)
    n.delete_instance()

    assert 'post_delete' in out.getvalue()


def test_timestampedmodel(table):
    n = TimeStampedNote.create(message='Hello')
    updated_at = n.updated_at
    with pytest.raises(peewee.IntegrityError):
        n.created_at = None
        n.save()

    n = TimeStampedNote.get(id=n.id)

    with pytest.raises(ValueError):
        n.published_at = datetime.datetime.utcnow()
        n.save()

    n.published_at = pendulum.now()
    n.save()
    assert n.updated_at > updated_at
    n1 = TimeStampedNote.get(id=n.id)
    rows = TimeStampedNote.update(message="Hellobw").where(TimeStampedNote.id==n.id).execute()
    assert rows == 1
    n2 = TimeStampedNote.get(id=n.id)
    assert n2.updated_at > n1.updated_at
    out = StringIO()

    def post_delete(sender, instance):
        out.write('post_delete received')

    signal.post_delete.connect(post_delete, sender=TimeStampedNote)
    n.delete_instance()

    assert 'post_delete' in out.getvalue()


def test_validator(table):
    note = Note()
    assert inspect.ismethod(note.validate_message)

    note.message = 'raise error'
    assert not note.is_valid()
    assert len(note.errors) > 0
    with pytest.raises(ValidationError):
        note.save()
    note.save(skip_validation=True)

    note.message = 'message'
    note._validate()
    note.save()
    assert note.message == Note.get_by_id(note.id).message


def test_instance_delete(table):
    note = Note.create(message='Hello')
    note.delete_instance()
    ins = Note.get_or_none(Note.id == note.id)
    assert ins is None
    out = StringIO()

    def post_delete(sender, instance):
        out.write(f'post_delete {sender}')

    def pre_delete(sender, instance):
        out.write(f'pre_delete {sender}')

    note2 = Note.create(message='Hello')
    signal.pre_delete.connect(pre_delete, sender=Note)
    signal.post_delete.connect(post_delete, sender=Note)
    note2.delete_instance()
    assert f'post_delete <Model: Note>' in out.getvalue()
    assert f'pre_delete <Model: Note>' in out.getvalue()
    out = StringIO()

    def post_delete(sender, instance):
        out.write(f'post_delete {sender}')

    def pre_delete(sender, instance):
        out.write(f'pre_delete {sender}')
    signal.pre_delete.connect(pre_delete, sender=Note)
    signal.post_delete.connect(post_delete, sender=Note)
    note3 = Note.create(message='Hello')
    note3.delete().execute()
    assert out.getvalue() == ""


def test_datetime():
    Note.create_table()
    dt = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
    n = Note(message='hello', published_at=dt)
    n.save()
    n = Note.get_by_id(n.id)
    assert n.published_at.timestamp() == dt.timestamp()
    Note.drop_table()


def test_json_field(table):
    note = Note.create(message='Hello')
    assert note.content == {}
    assert note.remark is None

    note.remark = None
    note.save()
    assert note.remark is None

    note = Note.create(message='Hello', content=['one', 'two'])
    assert note.content == ['one', 'two']

    note.content = [1, 2]
    note.save()
    note = Note.get_by_id(note.id)
    assert note.content == [1, 2]

    Note.update(content={'data': None}).where(Note.id == note.id).execute()
    note = Note.get_by_id(note.id)
    assert note.content == {'data': None}
    query_note = Note.get(content={'data': None})
    assert query_note.content == {'data': None}
    assert query_note.id == note.id


@pytest.fixture
def whitelistmodel():
    WhiteListNote.create_table()
    NoWhiteListNote.create_table()
    yield
    WhiteListNote.drop_table()
    NoWhiteListNote.drop_table()


def test_massassignment(whitelistmodel):
    m1 = WhiteListNote.create(f1=10, f2=10, f3=10, f4=10)
    assert m1.f1 == 10
    assert m1.f3 == 3
    assert m1.f4 == 4

    m1.update_with(f1=20, f2=20, f3=20, f4=20)
    assert m1.f1 == 20
    assert m1.f3 == 3
    assert m1.f4 == 4

    m1.f3 = 30
    m1.save()
    assert m1.f3 == 30

    m1 = WhiteListNote.get_by_id(m1.id)
    assert m1.f1 == 20
    assert m1.f3 == 30
    assert m1.f4 == 4

    m2 = NoWhiteListNote.create(f1=10, f2=10, f3=10, f4=10)
    assert m2.f1 == 10
    assert m2.f3 == 10
    assert m2.f4 == 4

    m2.update_with(f1=20, f2=20, f3=20, f4=20)
    assert m2.f1 == 20
    assert m2.f3 == 20
    assert m2.f4 == 4

    m2.f4 = 30
    m2.save()
    assert m2.f4 == 30

    m2 = NoWhiteListNote.get_by_id(m2.id)
    assert m2.f1 == 20
    assert m2.f3 == 20
    assert m2.f4 == 30
