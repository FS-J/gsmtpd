#!/usr/bin/env python
# encoding: utf-8

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.rst') as f:
    long_description = f.read()

with open('requirements.txt') as require:

    setup(name='gsmtpd',
            version='0.2',
            license='MIT',
            description='A smtpd server impletement based on Gevent',
            author='Meng Zhuo',
            author_email='mengzhuo1203@gmail.com',
            url='https://github.com/34nm/gsmtpd',
            packages=['gsmtpd'],
            install_requires=[line for line in require.readlines()],
            classifiers=[
                        'License :: OSI Approved :: MIT License',
                        'Programming Language :: Python :: 2',
                        'Programming Language :: Python :: 2.6',
                        'Programming Language :: Python :: 2.7',
                        'Topic :: Communications :: Email :: Mail Transport Agents',
                        'Topic :: Communications :: Email'
            ],
            platforms='any',
            long_description=long_description)
