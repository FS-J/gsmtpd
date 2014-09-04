#!/usr/bin/env python
# encoding: utf-8

from gevent import monkey
monkey.patch_all()

import smtplib

from .greentest import TestCase
from .utils import connect, run
from gsmtpd.server import SMTPServer

__all__ = ['ProcessRCPTServerTestCase', 'RCPTAPITestCase']

class ProcessRCPTServer(SMTPServer):

    def process_rcpt(self, address):

        if address != 'test@gsmtp.org':
            return "503 account %s not existed" % address

class ProcessRCPTServerTestCase(TestCase):


    def setUp(self):

        self.server = ProcessRCPTServer(('127.0.0.1',0))
        self.server.start()
        self.sm = smtplib.SMTP()

    @connect
    def test_rcpt_success(self):
        run(self.sm.helo)
        run(self.sm.mail, 'test@gsmtpd.org')
        self.assertEqual(run(self.sm.rcpt, 'test@gsmtp.org')[0], 250)

    @connect
    def test_rcpt_failed(self):
        run(self.sm.helo)
        run(self.sm.mail, 'test@gsmtpd.org')
        self.assertEqual(run(self.sm.rcpt, 'test@example.org'),
                        (503, 'account test@example.org not existed'))


class RCPTAPITestCase(TestCase):

    def setUp(self):

        self.server = SMTPServer(('127.0.0.1', 0))
        self.server.start()
        self.sm = smtplib.SMTP()

    @connect
    def test_not_block(self):

        run(self.sm.helo)
        run(self.sm.mail, 'test@gsmtpd.org')
        self.assertEqual(run(self.sm.rcpt, 'test@gsmtp.org')[0], 250)
