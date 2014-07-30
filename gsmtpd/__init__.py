#!/usr/bin/env python
# encoding: utf-8

"""
gsmtpd servers utils
---------------------

gsmtpd is a SMTP server implement based on Gevent library,
better in conccurence and more API

usage:

    >>> from gevent import monkey
    >>> monkey.patch_all()
    >>> from gsmtpd import SMTPServer
    >>> # then make your own SMTP server


"""

__title__ = 'gsmtpd'
__version__ = '0.1.9'
__author__ = 'Meng Zhuo <mengzhuo1203@gmail.com>'

from .server import SMTPServer, DebuggingServer, PureProxy

# Set default logging handler to avoid "No handler found" warnings.
import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
