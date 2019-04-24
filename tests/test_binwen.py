import os.path
from binwen import create_app
from binwen.test.stub import Stub

os.environ.setdefault('BINWEN_ENV', 'test')
root = os.path.join(os.path.dirname(__file__), 'binwenapp')
_app = create_app(root)


def test_binwen():
    from vip.models import Note
    Note.create_table()

    db = _app.extensions.db
    servicerclass = _app.servicers.VipServicer[1]

    stub = Stub(servicerclass())
    assert stub.return_normal(None)
    assert db.database.is_closed()

    Note.drop_table()
