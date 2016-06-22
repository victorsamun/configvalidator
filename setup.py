#!/usr/bin/env python3

import re
from setuptools import setup, find_packages


with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

with open('configchecker/__init__.py', encoding='utf-8') as f:
    for line in f:
        if '__version__' in line:
            version = re.findall(r"'(.*?)'", line)[0]

setup(
    name='configchecker',
    version=version,
    description='INI-config validator',
    long_description=long_description,
    url='https://github.com/victorsamun/configvalidator',
    download_url='https://github.com/victorsamun/configvalidator/archive/master.zip',
    author='Samun Victor',
    author_email='victor.samun@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='configparser configchecker checking validate',
    packages=find_packages()
)
