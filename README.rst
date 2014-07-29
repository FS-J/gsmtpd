gsmtpd
======


.. image:: https://travis-ci.org/34nm/gsmtpd.svg?branch=master

SMTP servers impletement base on Gevent

Install
----------

`pip install gsmtpd`

Usage
---------

Basically gsmtpd is ported from Python standard lib *smtpd*,
you can it check from Doc_

however there is only one difference, you should add monkey patch of gevent

.. code-block:: python

    from gevent import monkey
    monkey.patch_all()


Performance
---------------

The charts below shows gsmtpd vs asyncIO based smtpd in Python standrary lib.

.. note::

    Response per second = 0 means the program is crashed or refuse to connect



.. figure:: https://raw.githubusercontent.com/34nm/gsmtpd/master/helo_chart.png
    :scale: 100%

.. figure:: https://raw.githubusercontent.com/34nm/gsmtpd/master/mail_chart.png
    :scale: 100%


.. _Doc: https://docs.python.org/2/library/smtpd.html?highlight=smtpd#module-smtpd
