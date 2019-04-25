import pytest
import datetime

from peeweext.binwen import PeeweeExt


class App:
    config = dict(DATABASES={"default": {"DB_URL": "sqlite:///:memory:"}})


app = App()
db = PeeweeExt()
db.init_app(app)


class Note(db.Model):
    published_at = db.DatetimeTZField(null=True)
    content = db.JSONTextField(default={})
    remark = db.JSONTextField(null=True)


@pytest.fixture
def table():
    Note.create_table()
    yield
    Note.drop_table()


def test_fields(table):
    dt = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
    note = Note.create(published_at=dt)
    assert note.content == {}
    assert note.remark is None
    assert note.published_at.timestamp() == dt.timestamp()
    note.remark = None
    note.published_at = None
    note.save()
    assert note.remark is None
    assert note.published_at is None

    note = Note.create(content=('one', 'two'))
    assert note.content == ('one', 'two')

    note.content = [1, 2]
    note.published_at = "2019-03-24 17:49:14.353345+08:00"
    note.save()
    note = Note.get_by_id(note.id)
    assert note.content == [1, 2]
    assert note.published_at.in_tz(tz="Asia/Shanghai").to_datetime_string() == "2019-03-24 17:49:14"
    assert note.published_at.in_tz(tz="Asia/Shanghai").format("YYYY-MM-DD HH:mm:ss.SSSSSS") == "2019-03-24 17:49:14.353345"

    Note.update(content={'data': None}).where(Note.id == note.id).execute()
    note = Note.get_by_id(note.id)
    assert note.content == {'data': None}
    query_note = Note.get(content={'data': None})
    assert query_note.content == {'data': None}

