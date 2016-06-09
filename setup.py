#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='configchecker',
    version='0.9',
    description='INI-config validator',
    url='https://github.com/victorsamun/configvalidator',
    author='Samun Victor',
    author_email='victor.samun@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages()
)
