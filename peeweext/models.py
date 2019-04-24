import json
import inspect
import peewee
import pendulum

from peeweext.fields import DatetimeTZField
from peeweext.exceptions import ValidationError
from peeweext.signal import pre_init, post_delete, pre_delete, pre_save, post_save


class ModelMeta(peewee.ModelBase):
    def __new__(cls, name, bases, attrs):
        cls = super().__new__(cls, name, bases, attrs)
        cls._validators = {}
        for k, v in attrs.items():
            if k.startswith("validate_") and inspect.isfunction(v):
                fn = k[9:]
                if fn in cls._meta.fields:
                    cls._validators[fn] = v

        cls.__has_whitelist__ = getattr(cls._meta, "has_whitelist", False)
        cls.__accessible_fields__ = set(getattr(cls._meta, "accessible_fields", set()))
        cls.__protected_fields__ = set(getattr(cls._meta, "protected_fields", set()))

        return cls


class Model(peewee.Model, metaclass=ModelMeta):
    created_at = DatetimeTZField(default=pendulum.now)
    updated_at = DatetimeTZField(default=pendulum.now)

    def __init__(self, *args, **kwargs):
        pre_init.send(type(self), instance=self)
        self._validate_errors = None
        super().__init__(*args, **kwargs)

    @classmethod
    def create(cls, **query):
        return super().create(**cls._filter_attrs(query))

    def update_with(self, **query):
        for k, v in self._filter_attrs(query).items():
            setattr(self, k, v)
        return self.save()

    @classmethod
    def _filter_attrs(cls, attrs):
        if cls.__has_whitelist__:
            whitelist = cls.__accessible_fields__ - cls.__protected_fields__
            return {k: v for k, v in attrs.items() if k in whitelist}
        else:
            blacklist = cls.__protected_fields__ - cls.__accessible_fields__
            return {k: v for k, v in attrs.items() if k not in blacklist}

    def save(self, *args, **kwargs):
        skip_validation = kwargs.pop('skip_validation', False)
        if not skip_validation:
            if not self.is_valid():
                raise ValidationError(json.dumps(self._validate_errors))

        pk_value = self._pk
        created = kwargs.get('force_insert', False) or not bool(pk_value)
        pre_save.send(type(self), instance=self, created=created)
        ret = super().save(*args, **kwargs)
        post_save.send(type(self), instance=self, created=created)
        return ret

    def delete_instance(self, *args, **kwargs):
        pre_delete.send(type(self), instance=self)
        ret = super().delete_instance(*args, **kwargs)
        post_delete.send(type(self), instance=self)
        return ret

    def _validate(self):
        errors = {}

        for name, validator in self._validators.items():
            value = getattr(self, name)

            try:
                validator(self, value)
            except ValidationError as e:
                errors[name] = str(e.message)

        self._validate_errors = errors

    @property
    def errors(self):
        if self._validate_errors is None:
            self._validate()

        return self._validate_errors

    def is_valid(self):
        return not self.errors


def _touch_model(sender, instance, created):
    if issubclass(sender, Model):
        instance.updated_at = pendulum.now()


pre_save.connect(_touch_model)
