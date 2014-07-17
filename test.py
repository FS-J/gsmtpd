#!/usr/bin/env python
# encoding: utf-8

from gevent import monkey
monkey.patch_all()

from gsmtpd import DebuggingServer, SMTPServer, SMTPChannel, PureProxy

import unittest

class DebuggingServerTestCase(unittest.TestCase):

    def setUp(self):

        self.srv = DebuggingServer()
