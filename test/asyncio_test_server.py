#!/usr/bin/env python
# encoding: utf-8

import asyncore
from smtpd import SMTPServer

class P(SMTPServer):

    def process_message(self, *args, **kwargs):

        pass

s = P(('0.0.0.0', 5001), None)
asyncore.loop()

