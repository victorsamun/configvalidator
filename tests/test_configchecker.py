import configchecker as t
import functools
import unittest
from configparser import ConfigParser


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

    def test_not_validator(self):
        val = t.ItemNotValidator(t.ItemStringValidator("wrong"))
        self.assertIsInstance(val, t.ItemBaseValidator)
        self.assertTrue(val("not wrong"))
        self.assertTrue(val("ok"))
        self.assertFalse(val("wrong"))

    def test_or_validator(self):
        val = t.ItemOrValidator(
            t.ItemStringValidator("ok"), t.ItemStringValidator("fail"))
        self.assertIsInstance(val, t.ItemBaseValidator)
        self.assertTrue(val("ok"))
        self.assertTrue(val("fail"))
        self.assertFalse(val("error"))

    def test_and_validator(self):
        val = t.ItemAndValidator(
            t.ItemRegexValidator(r'.*a.*'), t.ItemRegexValidator(r'.*b.*'))
        self.assertIsInstance(val, t.ItemBaseValidator)
        self.assertTrue(val("xxabyy"))
        self.assertTrue(val("bxxayy"))
        self.assertFalse(val("xxayy"))
        self.assertFalse(val("xxbyy"))

    def test_count_validator(self):
        val = t.ItemCountValidator(t.ItemStringValidator("ok"),
                                   lambda x: x > 1)
        self.assertIsInstance(val, t.ItemBaseValidator)

        with self.subTest("one"):
            val.setup()
            val("ok")
            val("fail")
            self.assertFalse(val.teardown())

        with self.subTest("two"):
            val.setup()
            val("ok")
            val("fail")
            val("ok")
            self.assertTrue(val.teardown())

    def test_complex_count_validator(self):
        val = t.ItemAndValidator(
            t.ItemCountValidator(t.ItemStringValidator("ok"),
                                 lambda x: x > 1),
            t.ItemCountValidator(t.ItemStringValidator("ok"),
                                 lambda x: x < 3))

        with self.subTest("one"):
            val.setup()
            val("ok")
            self.assertFalse(val.teardown())

        with self.subTest("two"):
            val.setup()
            val("ok")
            val("ok")
            self.assertTrue(val.teardown())

        with self.subTest("three"):
            val.setup()
            val("ok")
            val("ok")
            val("ok")
            self.assertFalse(val.teardown())

    def test_factory(self):
        val = t.item_validator("TestVal", lambda x: x.title() == "String")()
        self.assertIsInstance(val, t.ItemBaseValidator)
        self.assertTrue(val("string"))
        self.assertTrue(val("STRING"))
        self.assertFalse(val("wrong"))


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

    @check_ok
    def test_sections_counter_ok_req(self):
        self.cfg.read_string("""
        [SECT_1]
        key = value

        [SECT_2]
        key = value

        [OPTIONAL]
        """)

        with self.schema.section(t.ItemCountValidator(
            t.ItemRegexValidator(r'SECT_\d+'), lambda x: x > 1)): pass

    @check_ok
    def test_sections_counter_ok_opt(self):
        self.cfg.read_string("""
        [GLOBAL]

        [OPT_1]
        key = value

        [OPT_2]
        key = value
        """)

        with self.schema.section(t.ItemCountValidator(
            t.ItemRegexValidator(r'OPT_\d+'), lambda x: x > 1),
            required=False): pass

    @check_fail
    def test_sections_counter_fail_req(self):
        self.cfg.read_string("""
        [SECT_1]
        key = value

        [OPTIONAL]
        """)

        with self.schema.section(t.ItemCountValidator(
            t.ItemRegexValidator(r'SECT_\d+'), lambda x: x > 1)): pass

    @check_fail
    def test_sections_counter_fail_opt(self):
        self.cfg.read_string("""
        [GLOBAL]

        [OPT_1]
        key = value
        """)

        with self.schema.section(t.ItemCountValidator(
            t.ItemRegexValidator(r'OPT_\d+'), lambda x: x > 1),
            required=False): pass

    @check_ok
    def test_values_counter_ok_req(self):
        self.cfg.read_string("""
        [GLOBAL]
        key_1 = value1
        key_2 = value2
        opt = optional
        """)

        with self.schema.section("GLOBAL") as s:
            s.value(t.ItemCountValidator(
                t.ItemRegexValidator(r'key_\d+'), lambda x: x > 1))

    @check_ok
    def test_values_counter_ok_opt(self):
        self.cfg.read_string("""
        [GLOBAL]
        key = value
        opt_1 = value1
        opt_2 = value2
        """)

        with self.schema.section("GLOBAL") as s:
            s.value(t.ItemCountValidator(
                t.ItemRegexValidator(r'opt_\d+'), lambda x: x > 1),
                required=False)

    @check_fail
    def test_values_counter_fail_req(self):
        self.cfg.read_string("""
        [GLOBAL]
        key_1 = value1
        opt = optional
        """)

        with self.schema.section("GLOBAL") as s:
            s.value(t.ItemCountValidator(
                t.ItemRegexValidator(r'key_\d+'), lambda x: x > 1))

    @check_fail
    def test_values_counter_fail_opt(self):
        self.cfg.read_string("""
        [GLOBAL]
        key = value
        opt_1 = value1
        """)

        with self.schema.section("GLOBAL") as s:
            s.value(t.ItemCountValidator(
                t.ItemRegexValidator(r'opt_\d+'), lambda x: x > 1),
                required=False)


if __name__ == '__main__':
    unittest.main()
