from configparser import ConfigParser
import configvalidator as t
import functools
import unittest


class ItemValidatorsTests(unittest.TestCase):
    def test_default_validator(self):
        val = t.ItemDefaultValidator()
        self.assertIsInstance(val, t.ItemBaseValidator)
        self.assertTrue(val("value"))
        self.assertTrue(val(None))

    def test_string_validator(self):
        val = t.ItemStringValidator("string")
        self.assertIsInstance(val, t.ItemBaseValidator)
        self.assertTrue(val("string"))
        self.assertFalse(val("String"))
        self.assertFalse(val("wrong"))

        val = t.ItemStringValidator("string", ignore_case=True)
        self.assertTrue(val("string"))
        self.assertTrue(val("String"))
        self.assertFalse(val("wrong"))

    def test_number_validator(self):
        val = t.ItemNumberValidator()
        self.assertIsInstance(val, t.ItemBaseValidator)
        self.assertTrue(val(42))
        self.assertTrue(val("42"))
        self.assertFalse(val(-12))
        self.assertFalse(val("-12"))
        self.assertFalse(val("wrong"))

    def test_regex_validator(self):
        val = t.ItemRegexValidator(r'[a-zA-Z]+')
        self.assertIsInstance(val, t.ItemBaseValidator)
        self.assertTrue(val("string"))
        self.assertTrue(val("SomeString"))
        self.assertFalse(val("some string"))
        self.assertFalse(val("str123"))
        self.assertFalse(val("123str"))


def check_ok(func):
    @functools.wraps(func)
    def wrapper(self):
        func(self)
        self.assertTrue(
            t.ConfigSchemaValidator(self.schema).validate(self.cfg))
    return wrapper


def check_fail(func):
    @functools.wraps(func)
    def wrapper(self):
        func(self)
        with self.assertRaises(t.ConfigError):
            t.ConfigSchemaValidator(self.schema).validate(self.cfg)
    return wrapper


class ConfigValidatorTest(unittest.TestCase):
    def setUp(self):
        self.cfg = ConfigParser()
        self.schema = t.ConfigSchema()

    @check_ok
    def test_sections_ok(self):
        self.cfg.read_string("""
        [GLOBAL]
        key = value

        [DATA]
        key1 = value1
        key2 = value2

        [OPTIONAL]
        """)

        with self.schema.section("GLOBAL"): pass
        with self.schema.section("DATA"): pass
        with self.schema.section("OPTIONAL", required=False): pass

    @check_ok
    def test_sections_noother_ok(self):
        self.cfg.read_string("""
        [GLOBAL]
        key = value
        """)

        with self.schema.section("GLOBAL"): pass
        with self.schema.section("OTHER", required=False): pass
        self.schema.no_other()

    @check_fail
    def test_sections_noother_fail(self):
        self.cfg.read_string("""
        [GLOBAL]
        key = value

        [OPTIONAL]
        """)

        with self.schema.section("GLOBAL"): pass
        self.schema.no_other()

    @check_fail
    def test_sections_fail(self):
        self.cfg.read_string("""
        [GLOBAL]
        key = value

        [OPTIONAL]
        """)

        with self.schema.section("GLOBAL"): pass
        with self.schema.section("DATA"): pass
        with self.schema.section("OPTIONAL", required=False): pass

    @check_ok
    def test_sections_multi_ok(self):
        self.cfg.read_string("""
        [SECT_1]
        key = value

        [SECT_2]
        key = value
        """)

        with self.schema.section(t.ItemRegexValidator(r'SECT_\d+')): pass
        self.schema.no_other()

    @check_fail
    def test_sections_multi_fail(self):
        self.cfg.read_string("""
        [SECT_1]
        key = value

        [SECT_2]
        key = value

        [OPTIONAL]
        """)

        with self.schema.section(t.ItemRegexValidator(r'SECT_\d+')): pass
        self.schema.no_other()

    @check_ok
    def test_values_ok(self):
        self.cfg.read_string("""
        [GLOBAL]
        key = value

        [OPTIONAL]
        key_1 = 10
        key_2 = 12
        key = value
        """)

        with self.schema.section("GLOBAL") as s:
            s.value("key", value_val="value").no_other()

        with self.schema.section("OPTIONAL", required=False) as s:
            s.value(t.ItemRegexValidator(r'key_\d+'),
                    value_val=t.ItemNumberValidator())

        self.schema.no_other()

    @check_fail
    def test_values_key_fail(self):
        self.cfg.read_string("""
        [GLOBAL]
        key = value
        aa = bb
        """)

        with self.schema.section("GLOBAL") as s:
            s.value("key").no_other()

    @check_fail
    def test_values_value_fail(self):
        self.cfg.read_string("""
        [GLOBAL]
        key = wrong
        """)

        with self.schema.section("GLOBAL") as s:
            s.value("key", value_val="value").no_other()

    @check_ok
    def test_values_opt_ok(self):
        self.cfg.read_string("""
        [GLOBAL]
        key = value
        """)

        with self.schema.section("GLOBAL") as s:
            s.value("key").value("optional", required=False).no_other()


if __name__ == '__main__':
    unittest.main()
