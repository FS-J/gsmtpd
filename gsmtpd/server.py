#!/usr/bin/env python
# encoding: utf-8

"""
An RFC 2821 smtp proxy Port from Python Standrad Library for gevent usage
"""

# Overview:
#
# This file implements the minimal SMTP protocol as defined in RFC 821.  It
# has a hierarchy of classes which implement the backend functionality for the
# smtpd.  A number of classes are provided:
#
#   SMTPServer - the base class for the backend.  Raises NotImplementedError
#   if you try to use it.
#
#   DebuggingServer - simply prints each message it receives on stdout.
#
#   PureProxy - Proxies all messages to a real smtpd which does final
#   delivery.  One known problem with this class is that it doesn't handle
#   SMTP errors from the backend server at all.  This should be fixed
#   (contributions are welcome!).
#
# Please note that this script requires Python 2.0
#
# Author: Barry Warsaw <barry@python.org>
#
# TODO:
#
# - support mailbox delivery
# - alias files
# - ESMTP
# - handle error codes from the backend smtpd

import logging
logger = logging.getLevelName(__name__)

from gevent import socket, monkey, sleep, Timeout
monkey.patch_all()
from gevent.server import StreamServer

from channel import SMTPChannel

__all__ = ["SMTPServer", "DebuggingServer", "PureProxy"]

class ConnectionTimeout(Exception):
    pass

NEWLINE = '\n'
EMPTYSTRING = ''
COMMASPACE = ', '

class SMTPServer(StreamServer):

    def handle(self, sock, addr):

        logger.info('Incomming connection %s:%s', *addr[:2])
        
        try:
            with Timeout(self.timeout, ConnectionTimeout):
                try:
                    sc = SMTPChannel(self, sock, addr)
                    while not sc.closed:
                        sc.handle_read()
                        sleep(0.1) # relieve CPU
                finally:
                    sc.close_when_done()

        except ConnectionTimeout:
            logger.warn('%s:%s Timeouted', *addr[:2])

        finally:
            if not sock.closed:
                sock.close()

    # API for "doing something useful with the message"
    def process_message(self, peer, mailfrom, rcpttos, data):
        """Override this abstract method to handle messages from the client.

        peer is a tuple containing (ipaddr, port) of the client that made the
        socket connection to our smtp port.

        mailfrom is the raw address the client claims the message is coming
        from.

        rcpttos is a list of raw addresses the client wishes to deliver the
        message to.

        data is a string containing the entire full text of the message,
        headers (if supplied) and all.  It has been `de-transparencied'
        according to RFC 821, Section 4.5.2.  In other words, a line
        containing a `.' followed by other text has had the leading dot
        removed.

        This function should return None, for a normal `250 Ok' response;
        otherwise it returns the desired response string in RFC 821 format.

        """
        raise NotImplementedError


class DebuggingServer(SMTPServer):
    # Do something with the gathered message
    def process_message(self, peer, mailfrom, rcpttos, data):
        inheaders = 1
        lines = data.split('\n')
        print '---------- MESSAGE FOLLOWS ----------'
        for line in lines:
            # headers first
            if inheaders and not line:
                print 'X-Peer:', peer[0]
                inheaders = 0
            print line
        print '------------ END MESSAGE ------------'


class PureProxy(SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data):
        lines = data.split('\n')
        # Look for the last header
        i = 0
        for line in lines:
            if not line:
                break
            i += 1
        lines.insert(i, 'X-Peer: %s' % peer[0])
        data = NEWLINE.join(lines)
        refused = self._deliver(mailfrom, rcpttos, data)
        # TBD: what to do with refused addresses?
        logger.debug('we got some refusals: %s', refused)

    def _deliver(self, mailfrom, rcpttos, data):
        import smtplib
        refused = {}
        try:
            s = smtplib.SMTP()
            s.connect(self._remoteaddr[0], self._remoteaddr[1])
            try:
                refused = s.sendmail(mailfrom, rcpttos, data)
            finally:
                s.quit()
        except smtplib.SMTPRecipientsRefused, e:
            logger.debug('got SMTPRecipientsRefused')
            refused = e.recipients
        except (socket.error, smtplib.SMTPException), e:
            logger.debug( 'got %s', e.__class__)
            # All recipients were refused.  If the exception had an associated
            # error code, use it.  Otherwise,fake it with a non-triggering
            # exception code.
            errcode = getattr(e, 'smtp_code', -1)
            errmsg = getattr(e, 'smtp_error', 'ignore')
            for r in rcpttos:
                refused[r] = (errcode, errmsg)
        return refused

