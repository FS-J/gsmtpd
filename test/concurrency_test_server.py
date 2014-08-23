from gevent import monkey
monkey.patch_all()


from gsmtpd import SMTPServer

class P(SMTPServer):

    def process_message(self, *args, **kwargs):

        pass

s = P(('0.0.0.0', 5000), timeout=180)
s.serve_forever()
