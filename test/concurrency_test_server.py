from gevent import monkey
monkey.patch_all()
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
)

from gsmtpd.server import SMTPServer

class P(SMTPServer):

    def process_message(self, *args, **kwargs):

        pass

s = P(('0.0.0.0', 5000), timeout=180)
s.serve_forever()
