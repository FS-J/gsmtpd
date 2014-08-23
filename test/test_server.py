#!/usr/bin/env python
# encoding: utf-8

import json
import os
import gevent
from gevent import monkey
monkey.patch_all()

import smtplib
from gsmtpd import SMTPServer
from greentest import TestCase

import logging

logging.basicConfig(level=logging.ERROR)

__all__ = ['SMTPServerTestCase','SimpleSMTPServerTestCase','SSLServerTestCase']
root_path = os.path.dirname(os.path.abspath(__file__))

def connect(func):

    def wrap(self, *args, **kwargs):
        
        task = gevent.spawn(self.sm.connect, '127.0.0.1', self.server.server_port)
        task.run()
        return func(self, *args, **kwargs)
    return wrap

def run(func, *args):
    task = gevent.spawn(func, *args)
    task.run()
    return task.value

class SMTPServerTestCase(TestCase):

    __timeout__ = 30

    def setUp(self):

        self.server = SMTPServer(('127.0.0.1', 0), timeout=1)
        self.server.start()
        gevent.sleep(0.01)
        self.sm = smtplib.SMTP()

    def test_connection(self):

        task = run(self.sm.connect,
                  '127.0.0.1', self.server.server_port)
        assert task[0] == 220

    @connect
    def test_HELO(self):
        
        assert run(self.sm.helo)[0] == 250

    @connect
    def test_EHLO(self):

        assert run(self.sm.ehlo) [0] == 250
        assert 'size' in self.sm.esmtp_features
        assert self.sm.esmtp_features['size'] >= 102400

    @connect
    def test_NOOP(self):
        assert run(self.sm.noop)[0] == 250
    
    @connect
    def test_HELP(self):
        
        assert 'running' in run(self.sm.help)
        assert 'github' in run(self.sm.help, 'ME')

    @connect
    def test_QUIT(self):

        assert 'Bye' in run(self.sm.quit)

    @connect
    def test_MAIL(self):
        assert run(self.sm.mail, '<test@example.com>')[0] == 250
        assert run(self.sm.mail, 'test@example.com>')[0] == 503


    @connect
    def test_RCPT(self):
        run(self.sm.mail, '<from@example.com>')
        assert run(self.sm.rcpt, '<target@example.com>')[0] == 250

    @connect
    def test_NEST_RCPT(self):
        assert run(self.sm.rcpt, '<target@example.com>')[0] == 503

    @connect
    def test_RSET(self):
        assert run(self.sm.rset)[0] == 250
        assert run(self.sm.rcpt, '<target@example.com>')[0] == 503

    @connect
    def test_timeout(self):
        gevent.sleep(self.server.timeout+1)
        self.assertRaises(smtplib.SMTPServerDisconnected, run, self.sm.mail, 'hi')

    def tearDown(self):
        self.sm.close()


class TmpFileMailServer(SMTPServer):


    def process_message(self, peer, mailfrom, rcpttos, data):

        import tempfile
        self.tmp = tempfile.mkstemp()[1]

        with open(self.tmp, 'w') as tmp:
            c = dict(peer=peer, mailfrom=mailfrom, 
                 rcpttos=rcpttos,data=data)

            tmp.write(json.dumps(c))
            tmp.flush()

    def clean(self):
        try:
            os.remove(self.tmp)
        except Exception:
            pass

class SimpleSMTPServerTestCase(TestCase):

    def setUp(self):

        self.server = TmpFileMailServer(('127.0.0.1', 0))
        self.server.start()
        gevent.sleep(0.01)
        self.sm = smtplib.SMTP()

    @connect
    def test_raw(self):

        self.sm.sendmail('test@example', ['aa@bb.com'], 'TESTMAIL')
        with open(self.server.tmp) as f:
            data = json.loads(f.read())

        self.assertEqual(data['mailfrom'],'<test@example> size=8')

        self.assertEqual(data['rcpttos'], ['aa@bb.com'])

        self.assertEqual(data['data'],'TESTMAIL')

    def tearDown(self):

        self.sm.close()
        self.server.clean()
   
class SSLServerTestCase(TestCase):

    def setUp(self):

        self.server = SMTPServer(('127.0.0.1', 0), 
                                 keyfile=os.path.join(root_path, 'server.key'),
                                 certfile=os.path.join(root_path, 'server.crt'))
        self.server.start()
        gevent.sleep(0.01)
        self.sm = smtplib.SMTP()
    
    @connect
    def test_STARTTLS(self):
        run(self.sm.ehlo)
        self.assertIn('starttls', self.sm.esmtp_features)
    
    @connect
    def test_handshake(self):
        run(self.sm.ehlo)
        self.assertEqual(run(self.sm.starttls)[0], 220)

    @connect
    def test_ssl_mail(self):
        run(self.sm.ehlo)
        run(self.sm.starttls)
        self.assertEqual(run(self.sm.mail, 'test@gsmtpd.org')[0], 250)


    def tearDown(self):

        self.sm.close()
