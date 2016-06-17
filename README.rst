configchecker
-------------
This module helps to check ``configparser``-loaded configurations.

Usage
=====

1. Initialize description of valid configuration:
   ``schema = configchecker.ConfigSchema()``
2. Add an information of possible sections by calling ``schema.section`` with section name validator and boolean flag „section required“.
3. In every section describe possible section's values by calling ``sect.value``.

Name/value validators
=====================

There are basic validators:
* ``ItemDefaultValidator`` — always returns true
* ``ItemStringValidator`` — checks if a string equals to given (probably, case-insensitive)
* ``ItemRegexValidator`` — checks matching a string to given regexp
* ``ItemNumberValidator`` — checks that a string is a non-negative integer

And validator-composers which allow to create more complex checks:
* ``ItemNotValidator``, ``ItemAndValidator``, ``ItemOrValidator`` — first-order logic on validators
* ``ItemCountValidator`` — takes a validator and a function that check number of validator's true positives (i.e. returns ``True``)

Examples
========

.. code-block:: py
    import configparser
    import configchecker as v
    
    config = configparser.ConfigParser()
    config.read_file("config")
    
    schema = v.ConfigSchema()
    
    # Section with name „REQUIRED“ will be mandatory
    with schema.section("REQUIRED") as s:
      # It must have keys matching regexp r'item_\d+' and numeric value and nothing more
      s.value(v.ItemRegexValidator(r'item_\d+', value_val=v.ItemNumberValidator()).no_other()
      
    # Section with name r'OPT_\w+' (check by regexp) will be optional
    with schema.section(v.ItemRegexValidator(r'OPT_\w+'), required=False) as s:
      # And it may have anything
      pass
      
    # Other sections will be restricted
    schema.no_other()
    
    # Run checks
    v.ConfigSchemaValidator(schema).validate(config)

Also, you can find lots of examples in tests (``test_configchecker.py``)


Author
======

Samun Victor, victor.samun@gmail.com
