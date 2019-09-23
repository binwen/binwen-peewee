from datetime import datetime

import pytest
import peeweext
from peeweext.binwen import PeeweeExt
from peeweext.paginator import Paginator, InvalidPage, PageNotAnInteger, EmptyPage, Page


def check_paginator(params, output):
    count, num_pages = output
    paginator = Paginator(*params)
    check_attribute('count', paginator, count, params)
    check_attribute('num_pages', paginator, num_pages, params)


def check_attribute(name, paginator, expected, params, coerce=None):
    got = getattr(paginator, name)
    if coerce is not None:
        got = coerce(got)
    assert expected == got, f"For '{name}', expected {expected} but got {got}.  Paginator parameters were: {params}"


def test_paginator():
    nine = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    ten = nine + [10]
    eleven = ten + [11]
    tests = (
        ((ten, 4, 0, False), (10, 3)),
        ((ten, 4, 1, False), (10, 3)),
        ((ten, 4, 2, False), (10, 2)),
        ((ten, 4, 5, False), (10, 2)),
        ((ten, 4, 6, False), (10, 1)),
        ((ten, 4, 0, True), (10, 3)),
        ((ten, 4, 1, True), (10, 3)),
        ((ten, 4, 2, True), (10, 2)),
        ((ten, 4, 5, True), (10, 2)),
        ((ten, 4, 6, True), (10, 1)),
        # One item, varying orphans, no empty first page.
        (([1], 4, 0, False), (1, 1)),
        (([1], 4, 1, False), (1, 1)),
        (([1], 4, 2, False), (1, 1)),
        # One item, varying orphans, allow empty first page.
        (([1], 4, 0, True), (1, 1)),
        (([1], 4, 1, True), (1, 1)),
        (([1], 4, 2, True), (1, 1)),
        # Zero items, varying orphans, no empty first page.
        (([], 4, 0, False), (0, 0)),
        (([], 4, 1, False), (0, 0)),
        (([], 4, 2, False), (0, 0)),
        # Zero items, varying orphans, allow empty first page.
        (([], 4, 0, True), (0, 1)),
        (([], 4, 1, True), (0, 1)),
        (([], 4, 2, True), (0, 1)),
        # Number if items one less than per_page.
        (([], 1, 0, True), (0, 1)),
        (([], 1, 0, False), (0, 0)),
        (([1], 2, 0, True), (1, 1)),
        ((nine, 10, 0, True), (9, 1)),
        # Number if items equal to per_page.
        (([1], 1, 0, True), (1, 1)),
        (([1, 2], 2, 0, True), (2, 1)),
        ((ten, 10, 0, True), (10, 1)),
        # Number if items one more than per_page.
        (([1, 2], 1, 0, True), (2, 2)),
        (([1, 2, 3], 2, 0, True), (3, 2)),
        ((eleven, 10, 0, True), (11, 2)),
        # Number if items one more than per_page with one orphan.
        (([1, 2], 1, 1, True), (2, 1)),
        (([1, 2, 3], 2, 1, True), (3, 1)),
        ((eleven, 10, 1, True), (11, 1)),
        # Non-integer inputs
        ((ten, '4', 1, False), (10, 3)),
        ((ten, '4', 1, False), (10, 3)),
        ((ten, 4, '1', False), (10, 3)),
        ((ten, 4, '1', False), (10, 3)),
    )
    for params, output in tests:
        check_paginator(params, output)


def test_invalid_page_number():
    paginator = Paginator([1, 2, 3], 2)
    with pytest.raises(PageNotAnInteger):
        paginator.validate_number(None)
    with pytest.raises(PageNotAnInteger):
        paginator.validate_number('x')
    with pytest.raises(PageNotAnInteger):
        paginator.validate_number(1.2)


def test_float_integer_page():
    paginator = Paginator([1, 2, 3], 2)
    assert paginator.validate_number(1.0) == 1


def test_no_content_allow_empty_first_page():
    paginator = Paginator([], 2)
    assert paginator.validate_number(1) == 1


def test_paginate_misc_classes():
    class CountContainer:
        def count(self):
            return 42

    paginator = Paginator(CountContainer(), 10)
    assert 42 == paginator.count
    assert 5 == paginator.num_pages

    class LenContainer:
        def __len__(self):
            return 42

    paginator = Paginator(LenContainer(), 10)
    assert 42 == paginator.count
    assert 5 == paginator.num_pages


def check_indexes(params, page_num, indexes):

    paginator = Paginator(*params)
    if page_num == 'first':
        page_num = 1
    elif page_num == 'last':
        page_num = paginator.num_pages
    page = paginator.page(page_num)
    start, end = indexes
    msg = "For %s of page %s, expected %s but got %s. Paginator parameters were: %s"
    assert start == page.start_index(), msg % ('start index', page_num, start, page.start_index(), params)
    assert end == page.end_index(), msg % ('end index', page_num, end, page.end_index(), params)


def test_page_indexes():
    ten = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    tests = (
        ((ten, 1, 0, True), (1, 1), (10, 10)),
        ((ten, 2, 0, True), (1, 2), (9, 10)),
        ((ten, 3, 0, True), (1, 3), (10, 10)),
        ((ten, 5, 0, True), (1, 5), (6, 10)),
        # Ten items, varying per_page, with orphans.
        ((ten, 1, 1, True), (1, 1), (9, 10)),
        ((ten, 1, 2, True), (1, 1), (8, 10)),
        ((ten, 3, 1, True), (1, 3), (7, 10)),
        ((ten, 3, 2, True), (1, 3), (7, 10)),
        ((ten, 3, 4, True), (1, 3), (4, 10)),
        ((ten, 5, 1, True), (1, 5), (6, 10)),
        ((ten, 5, 2, True), (1, 5), (6, 10)),
        ((ten, 5, 5, True), (1, 10), (1, 10)),
        # One item, varying orphans, no empty first page.
        (([1], 4, 0, False), (1, 1), (1, 1)),
        (([1], 4, 1, False), (1, 1), (1, 1)),
        (([1], 4, 2, False), (1, 1), (1, 1)),
        # One item, varying orphans, allow empty first page.
        (([1], 4, 0, True), (1, 1), (1, 1)),
        (([1], 4, 1, True), (1, 1), (1, 1)),
        (([1], 4, 2, True), (1, 1), (1, 1)),
        # Zero items, varying orphans, allow empty first page.
        (([], 4, 0, True), (0, 0), (0, 0)),
        (([], 4, 1, True), (0, 0), (0, 0)),
        (([], 4, 2, True), (0, 0), (0, 0)),
    )
    for params, first, last in tests:
        check_indexes(params, 'first', first)
        check_indexes(params, 'last', last)


def test_page_sequence():
    eleven = 'abcdefghijk'
    page2 = Paginator(eleven, page_size=5, orphans=1).page(2)
    assert len(page2) == 6
    assert 'k' in page2
    assert 'a' not in page2
    assert ''.join(page2) == 'fghijk'
    assert ''.join(reversed(page2)) == 'kjihgf'


class ValidAdjacentNumsPage(Page):

    def next_page_number(self):
        if not self.has_next():
            return None
        return super().next_page_number()

    def previous_page_number(self):
        if not self.has_previous():
            return None
        return super().previous_page_number()


class ValidAdjacentNumsPaginator(Paginator):

    def _get_page(self, *args, **kwargs):
        return ValidAdjacentNumsPage(*args, **kwargs)


def test_get_page_hook():
    eleven = 'abcdefghijk'
    paginator = ValidAdjacentNumsPaginator(eleven, page_size=6)
    page1 = paginator.page(1)
    page2 = paginator.page(2)
    assert page1.previous_page_number() is None
    assert page1.next_page_number() == 2
    assert page2.previous_page_number() == 1
    assert page2.next_page_number() is None


def test_get_page():
    paginator = Paginator([1, 2, 3], 2)
    page = paginator.page(1)
    assert page.page_number == 1
    assert page.object_list == [1, 2]
    assert paginator.page(3).page_number == 2
    assert paginator.page(None).page_number == 1


def test_get_page_empty_object_list():
    paginator = Paginator([], 2)
    assert paginator.page(1).page_number == 1
    assert paginator.page(2).page_number == 1
    assert paginator.page(None).page_number == 1


def test_get_page_empty_object_list_and_allow_empty_first_page_false():
    paginator = Paginator([], 2, allow_empty_first_page=False)
    assert paginator.page(1).num_pages == 0


class App:
    config = dict(DATABASES={"default": {"DB_URL": "sqlite:///:memory:"}})


app = App()
db = PeeweeExt()
db.init_app(app)


class Article(db.Model):
    headline = peeweext.CharField(max_length=100, default='Default headline')
    pub_date = peeweext.DateTimeField()

    def __str__(self):
        return self.headline


@pytest.fixture
def table():
    Article.create_table()
    for x in range(1, 10):
        a = Article(headline='Article %s' % x, pub_date=datetime(2005, 7, 29))
        a.save()
    yield
    Article.drop_table()


def test_first_page(table):
    paginator = Paginator(Article.select().order_by('id'), 5)
    p = paginator.page(1)
    assert "<Page 1 of 2>" == str(p)
    assert [str(s) for s in p.object_list] == [
        "Article 1",
        "Article 2",
        "Article 3",
        "Article 4",
        "Article 5"
    ]
    assert p.has_next() is True
    assert p.has_previous() is False
    assert p.has_other_pages() is True
    assert 2 == p.next_page_number()
    with pytest.raises(InvalidPage):
        p.previous_page_number()
    assert 1 == p.start_index()
    assert 5 == p.end_index()


def test_last_page(table):
    paginator = Paginator(Article.select().order_by('id'), 5)
    p = paginator.page(2)
    assert "<Page 2 of 2>" == str(p)
    assert [str(s) for s in p.object_list] == [
        "Article 6",
        "Article 7",
        "Article 8",
        "Article 9"
    ]
    assert p.has_next() is False
    assert p.has_previous() is True
    assert p.has_other_pages() is True
    with pytest.raises(InvalidPage):
        p.next_page_number()
    assert 1 == p.previous_page_number()
    assert 6 == p.start_index()
    assert 9 == p.end_index()


def test_page_getitem(table):
    paginator = Paginator(Article.select().order_by('id'), 5)
    p = paginator.page(1)

    with pytest.raises(TypeError):
        p['has_previous']
    assert not isinstance(p.object_list, list)
    assert p[0] == Article.select().filter(headline='Article 1').get()
    assert [str(s) for s in p[slice(2)]] == [
        "Article 1",
        "Article 2",
    ]
    assert isinstance(p.object_list, list)
