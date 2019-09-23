"""
分页
"""
from collections.abc import Sequence

from math import ceil
from peewee import Query


class UnorderedObjectListWarning(RuntimeWarning):
    pass


class InvalidPage(Exception):
    pass


class PageNotAnInteger(InvalidPage):
    pass


class EmptyPage(InvalidPage):
    pass


class Paginator:
    def __init__(self, queryset, page_size=20, orphans=0, allow_empty_first_page=True):
        self.queryset = queryset
        self.page_size = int(page_size)
        self.orphans = int(orphans)
        self._num_pages = self._count = None
        self.allow_empty_first_page = allow_empty_first_page

    def validate_number(self, number):
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger("页码不是整数")

        if number < 1:
            raise EmptyPage("页码小于1")

        if number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage("该分页不包含任何结果")

        return number

    def page(self, page_number):
        try:
            number = self.validate_number(page_number)
        except PageNotAnInteger:
            number = 1
        except EmptyPage:
            number = self.num_pages

        bottom = (number - 1) * self.page_size
        if isinstance(self.queryset, Query):
            if bottom + self.orphans >= self.count:
                bottom = self.count
            object_list = self.queryset.limit(self.page_size).offset(bottom)
        else:
            top = bottom + self.page_size
            if top + self.orphans >= self.count:
                top = self.count
            object_list = self.queryset[bottom:top]

        return self._get_page(object_list, number, self)

    @staticmethod
    def _get_page(*args, **kwargs):
        return Page(*args, **kwargs)

    @property
    def count(self):
        if self._count is None:
            try:
                self._count = self.queryset.count()
            except (AttributeError, TypeError):
                self._count = len(self.queryset)

        return self._count

    @property
    def num_pages(self):
        if self._num_pages is None:
            if self.count == 0 and not self.allow_empty_first_page:
                self._num_pages = 0
            else:
                hits = max(1, self.count - self.orphans)
                self._num_pages = int(ceil(hits / float(self.page_size)))

        return self._num_pages


class Page(Sequence):

    def __init__(self, object_list, page_number, paginator):
        self.object_list = object_list
        self.page_number = page_number
        self.paginator = paginator

    def __repr__(self):
        return '<Page %s of %s>' % (self.page_number, self.paginator.num_pages)

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        if not isinstance(index, (int, slice)):
            raise TypeError
        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)

        return self.object_list[index]

    def has_next(self):
        return self.page_number < self.paginator.num_pages

    def has_previous(self):
        return self.page_number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        return self.paginator.validate_number(self.page_number + 1)

    def previous_page_number(self):
        return self.paginator.validate_number(self.page_number - 1)

    def start_index(self):
        if self.paginator.count == 0:
            return 0
        return (self.paginator.page_size * (self.page_number - 1)) + 1

    def end_index(self):
        if self.page_number == self.paginator.num_pages:
            return self.paginator.count
        return self.page_number * self.paginator.page_size

    @property
    def count(self):
        return self.paginator.count

    @property
    def num_pages(self):
        return self.paginator.num_pages
