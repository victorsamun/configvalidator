"""Module for config validation"""

import configparser
import functools
import re
from contextlib import contextmanager, suppress
from collections import namedtuple, defaultdict
from itertools import chain as iter_chain


__version__ = '0.95'
__all__ = [
    'ConfigSchema',
    'ConfigSchemaValidator',

    'ConfigError',

    'ItemBaseValidator',
    'ItemDefaultValidator',

    'ItemNotValidator',
    'ItemOrValidator',
    'ItemAndValidator',
    'ItemCountValidator',

    'ItemStringValidator',
    'ItemRegexValidator',
    'ItemNumberValidator',
    'item_validator',
]


class ItemBaseValidator:
    """Base class for item validators"""
    def setup(self):
        pass

    def __call__(self, value):
        raise NotImplemented

    def teardown(self):
        return True


def item_validator(name, func):
    """Class factory for item validators"""
    return type(name, (ItemBaseValidator,),
                {
                    '__call__': lambda self, x: func(x),
                    'setup':    lambda self: None,
                    'teardown': lambda self: True
                })


ItemDefaultValidator = item_validator('ItemDefaultValidator', lambda _: True)


def _validator_safe_call(validator, value):
    with suppress(Exception):
        return validator(value)
    return False


class ItemNotValidator(ItemBaseValidator):
    """Logical NOT"""
    def __init__(self, validator):
        if not isinstance(validator, ItemBaseValidator):
            raise TypeError('validator')

        self.validator = validator

    def setup(self):
        self.validator.setup()

    def __call__(self, value):
        """Returns `True` if `validator` returns `False` or fail"""
        return not _validator_safe_call(self.validator, value)

    def teardown(self):
        """Returns `True` if `validator` ends with `False`"""
        return not self.validator.teardown()


class ItemOrValidator(ItemBaseValidator):
    """Logical OR"""
    def __init__(self, *validators):
        if not all(isinstance(val, ItemBaseValidator) for val in validators):
            raise TypeError('validators')

        self.validators = validators

    def setup(self):
        for val in self.validators:
            val.setup()

    def __call__(self, value):
        """Returns `True` if any `validators` returns `True`"""
        return any(_validator_safe_call(val, value) for val in self.validators)

    def teardown(self):
        """Returns `True` if any `validators` ends with `True`"""
        return any(val.teardown() for val in self.validators)


class ItemAndValidator(ItemBaseValidator):
    """Logical AND"""
    def __init__(self, *validators):
        if not all(isinstance(val, ItemBaseValidator) for val in validators):
            raise TypeError('validators')

        self.validators = validators

    def setup(self):
        for val in self.validators:
            val.setup()

    def __call__(self, value):
        """Returns `True` if all `validators` returns `True`"""
        return all(_validator_safe_call(val, value) for val in self.validators)

    def teardown(self):
        """Returns `True` if all `validators` ends with `True`"""
        return all(val.teardown() for val in self.validators)


class ItemCountValidator(ItemBaseValidator):
    """Counting validator"""
    def __init__(self, validator, check_fn):
        """Initializes counting validator by a `validator` and counting
        function `check_fn`"""
        if not isinstance(validator, ItemBaseValidator):
            raise TypeError('validator')

        if not callable(check_fn):
            raise TypeError('check_fn')

        self.validator = validator
        self.check_fn = check_fn
        self.setup()

    def setup(self):
        self.count = 0

    def __call__(self, value):
        """Returns `True` if `validator` returns `True`"""
        if _validator_safe_call(self.validator, value):
            self.count += 1
            return True

        return False

    def teardown(self):
        """Returns `True` if `check_fn` accepts number of successed calls
        underlying `validator`"""
        return self.check_fn(self.count)


class ItemStringValidator(ItemBaseValidator):
    """String validator"""
    def __init__(self, expected, ignore_case=False):
        if not isinstance(expected, str):
            raise TypeError('expected')

        self.value = expected
        self.ign = ignore_case

    def __call__(self, value):
        """Returns `True` if `value` is equals to `expected`"""
        if self.ign:
            return self.value.casefold() == value.casefold()

        return self.value == value


class ItemRegexValidator(ItemBaseValidator):
    """Regular expression validator"""
    def __init__(self, regex):
        self.regexp = re.compile(regex)

    def __call__(self, value):
        """Returns `True` if `regex` full matches `value`"""
        return bool(self.regexp.fullmatch(value))


class ItemNumberValidator(ItemBaseValidator):
    """Non-negative number validator"""
    def __call__(self, value):
        """Returns `True` if `value` may be interpreted as non-negative
        number"""
        try:
            return int(value) >= 0
        except ValueError:
            return False


_ValidatorItem = namedtuple('_ValidatorItem', ('key_val', 'value_val'))


class _BaseValidator:
    def __init__(self):
        self.reqs = []
        self.opts = []
        self.fail_other = False

    def _add_value(self, key, value, required=True):
        ptr_vals = self.reqs if required else self.opts
        ptr_vals.append(_ValidatorItem(key, value))
        return self

    @staticmethod
    def _norm_key(key, name):
        if not isinstance(key, (str, ItemBaseValidator)):
            raise TypeError(name)

        return ItemStringValidator(key) if isinstance(key, str) else key

    def no_other(self):
        self.fail_other = True
        return self


class _SectionValidator(_BaseValidator):
    """Allows to describe a scheme for section of config validation"""
    def value(self, key_val, required=True,
              value_val=ItemDefaultValidator()):
        """Describes a values in a section in configuration. `key_val` is
        validator for key of value, `value_val` is validator for value of
        value"""
        key = _BaseValidator._norm_key(key_val, 'key_val')
        value_ = _BaseValidator._norm_key(value_val, 'value_val')

        return self._add_value(key, value_, required)


class ConfigSchema(_BaseValidator):
    """Allows to describe a scheme for config validation"""
    @contextmanager
    def section(self, name_val, required=True):
        """Describes a section in configuration. `name_val` is validator for
        section name"""
        name = _BaseValidator._norm_key(name_val, 'name_val')

        validator = _SectionValidator()
        yield validator
        self._add_value(name, validator, required)


class ConfigError(Exception):
    """Base exception-class for validation errors"""
    def __str__(self):
        return self.message


class UnexpectedSectionsError(ConfigError):
    def __init__(self, section_names):
        self.message = 'Unexpected sections with names: "{}"'.format(
            ', '.join(section_names))


class ExpectedSectionsError(ConfigError):
    def __init__(self):
        self.message = 'Other sections expected'


class UnexpectedValuesError(ConfigError):
    def __init__(self, section, value_names):
        self.message = 'Unexpected values: "{}" in section "{}"'.format(
            ', '.join(value_names), section)


class ExpectedValuesError(ConfigError):
    def __init__(self, section):
        self.message = 'Other values expected in section "{}"'.format(section)


class ValueValidationError(ConfigError):
    def __init__(self, val, section, key, validator_name):
        self.message = ('Wrong value in section "{}", key "{}": '
                        '"{}" ({})').format(section, key, val, validator_name)


class ConfigSchemaValidator:
    """Validator engine"""
    def __init__(self, schema):
        """Initializes validator by `ConfigSchema`"""
        if not isinstance(schema, ConfigSchema):
            raise TypeError('schema')

        self._schema = schema

    def validate(self, config):
        """Validates `config` which is `ConfigParser` by schema.
        Returns `True` if config is valid or raises `ConfigError` otherwise"""
        if not isinstance(config, configparser.ConfigParser):
            raise TypeError('config')

        ConfigSchemaValidator._validate_config(config, self._schema)
        return True

    @staticmethod
    def _validate(items, schema, next_validator):
        req_validators = list(schema.reqs)
        req_vals_pass = [False]*len(req_validators)
        other = []

        for val in iter_chain(schema.reqs, schema.opts):
            val.key_val.setup()

        for (name, value) in items:
            for (i, validator) in enumerate(req_validators):
                if _validator_safe_call(validator.key_val, name):
                    req_vals_pass[i] = True
                    next_validator(value, validator.value_val, name)
                    break
            else:
                for validator in schema.opts:
                    if _validator_safe_call(validator.key_val, name):
                        next_validator(value, validator.value_val, name)
                        break
                else:
                    other.append(name)

        all_completed = all(val.key_val.teardown()
                            for val in iter_chain(schema.reqs, schema.opts))
        return (all(req_vals_pass) and all_completed, other)

    @staticmethod
    def _check(validate_rv, schema, ok_exc, other_exc):
        (ok, other) = validate_rv

        if not ok:
            raise ok_exc

        if other and schema.fail_other:
            raise other_exc

    @staticmethod
    def _validate_config(config, schema):
        rv = ConfigSchemaValidator._validate(
            ((name, config[name]) for name in config.sections()), schema,
            ConfigSchemaValidator._validate_section)

        ConfigSchemaValidator._check(
            rv, schema, ExpectedSectionsError(),
            UnexpectedSectionsError(rv[1]))

    @staticmethod
    def _validate_section(section, schema, sect_name):
        rv = ConfigSchemaValidator._validate(
            section.items(), schema, functools.partial(
                ConfigSchemaValidator._validate_value, section=sect_name))

        ConfigSchemaValidator._check(
            rv, schema, ExpectedValuesError(sect_name),
            UnexpectedValuesError(sect_name, rv[1]))

    @staticmethod
    def _validate_value(value, validator, key, section):
        err = ValueValidationError(value, section, key,
                                   type(validator).__name__)
        try:
            rv = validator(value)
        except Exception as e:
            raise err from e

        if not rv:
            raise err
