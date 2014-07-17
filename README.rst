gsmtpd
======

SMTP servers impletement base on Gevent

Install
----------

`pip install gsmtpd`

Usage
---------

Basically gsmtp is ported from Python standard lib *smtpd*,
you can it check from Doc_

however there is only one difference, you should add monkey patch of gevent

.. code-block:: python

    from gevent import monkey
    monkey.patch_all()




.. _Doc: https://docs.python.org/2/library/smtpd.html?highlight=smtpd#module-smtpd
