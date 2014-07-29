import gevent
import sys
import gc
from functools import wraps
import re

import os
from os.path import basename, splitext
from unittest import TestCase as BaseTestCase

gettotalrefcount = getattr(sys, 'gettotalrefcount', None)

# By default, test cases are expected to switch and emit warnings if there was none
# If a test is found in this list, it's expected not to switch.
no_switch_tests = '''test_patched_select.SelectTestCase.test_error_conditions
test_patched_ftplib.*.test_all_errors
test_patched_ftplib.*.test_getwelcome
test_patched_ftplib.*.test_sanitize
test_patched_ftplib.*.test_set_pasv
#test_patched_ftplib.TestIPv6Environment.test_af
test_patched_socket.TestExceptions.testExceptionTree
test_patched_socket.Urllib2FileobjectTest.testClose
test_patched_socket.TestLinuxAbstractNamespace.testLinuxAbstractNamespace
test_patched_socket.TestLinuxAbstractNamespace.testMaxName
test_patched_socket.TestLinuxAbstractNamespace.testNameOverflow
test_patched_socket.FileObjectInterruptedTestCase.*
test_patched_urllib.*
test_patched_asyncore.HelperFunctionTests.*
test_patched_httplib.BasicTest.*
test_patched_httplib.HTTPSTimeoutTest.test_attributes
test_patched_httplib.HeaderTests.*
test_patched_httplib.OfflineTest.*
test_patched_httplib.HTTPSTimeoutTest.test_host_port
test_patched_httplib.SourceAddressTest.testHTTPSConnectionSourceAddress
test_patched_select.SelectTestCase.test_error_conditions
test_patched_smtplib.NonConnectingTests.*
test_patched_urllib2net.OtherNetworkTests.*
test_patched_wsgiref.*
test_patched_subprocess.HelperFunctionTests.*
'''

ignore_switch_tests = '''
test_patched_socket.GeneralModuleTests.*
test_patched_httpservers.BaseHTTPRequestHandlerTestCase.*
test_patched_queue.*
test_patched_signal.SiginterruptTest.*
test_patched_urllib2.*
test_patched_ssl.*
test_patched_signal.BasicSignalTests.*
test_patched_threading_local.*
test_patched_threading.*
'''


def make_re(tests):
    tests = [x.strip().replace('\.', '\\.').replace('*', '.*?') for x in tests.split('\n') if x.strip()]
    tests = re.compile('^%s$' % '|'.join(tests))
    return tests



no_switch_tests = make_re(no_switch_tests)
ignore_switch_tests = make_re(ignore_switch_tests)

def get_switch_expected(fullname):
    if ignore_switch_tests.match(fullname) is not None:
        return None
    if no_switch_tests.match(fullname) is not None:
        return False
    return True

def wrap_refcount(method):
    if gettotalrefcount is None:
        return method

    @wraps(method)
    def wrapped(self, *args, **kwargs):
        gc.collect()
        gc.collect()
        gc.collect()
        deltas = []
        d = None
        gc.disable()
        try:
            while True:
                d = gettotalrefcount()
                self.setUp()
                method(self, *args, **kwargs)
                self.tearDown()
                if 'urlparse' in sys.modules:
                    sys.modules['urlparse'].clear_cache()
                if 'urllib.parse' in sys.modules:
                    sys.modules['urllib.parse'].clear_cache()
                d = gettotalrefcount() - d
                deltas.append(d)
                # the following configurations are classified as "no leak"
                # [0, 0]
                # [x, 0, 0]
                # [... a, b, c, d]  where a+b+c+d = 0
                #
                # the following configurations are classified as "leak"
                # [... z, z, z]  where z > 0
                if deltas[-2:] == [0, 0] and len(deltas) in (2, 3):
                    break
                elif deltas[-3:] == [0, 0, 0]:
                    break
                elif len(deltas) >= 4 and sum(deltas[-4:]) == 0:
                    break
                elif len(deltas) >= 3 and deltas[-1] > 0 and deltas[-1] == deltas[-2] and deltas[-2] == deltas[-3]:
                    raise AssertionError('refcount increased by %r' % (deltas, ))
                # OK, we don't know for sure yet. Let's search for more
                if sum(deltas[-3:]) <= 0 or sum(deltas[-4:]) <= 0 or deltas[-4:].count(0) >= 2:
                    # this is suspicious, so give a few more runs
                    limit = 11
                else:
                    limit = 7
                if len(deltas) >= limit:
                    raise AssertionError('refcount increased by %r' % (deltas, ))
        finally:
            gc.enable()
        self.skipTearDown = True

    return wrapped


def wrap_error_fatal(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        # XXX should also be able to do gevent.SYSTEM_ERROR = object
        # which is a global default to all hubs
        SYSTEM_ERROR = gevent.get_hub().SYSTEM_ERROR
        gevent.get_hub().SYSTEM_ERROR = object
        try:
            return method(self, *args, **kwargs)
        finally:
            gevent.get_hub().SYSTEM_ERROR = SYSTEM_ERROR
    return wrapped


def wrap_restore_handle_error(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        old = gevent.get_hub().handle_error
        try:
            return method(self, *args, **kwargs)
        finally:
            gevent.get_hub().handle_error = old
        if self.peek_error()[0] is not None:
            gevent.getcurrent().throw(*self.peek_error()[1:])
    return wrapped

def wrap_timeout(timeout, method):
    if timeout is None:
        return method

    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with gevent.Timeout(timeout, 'test timed out', ref=False):
            return method(self, *args, **kwargs)

    return wrapped

def _get_class_attr(classDict, bases, attr, default=AttributeError):
    NONE = object()
    value = classDict.get(attr, NONE)
    if value is not NONE:
        return value
    for base in bases:
        value = getattr(bases[0], attr, NONE)
        if value is not NONE:
            return value
    if default is AttributeError:
        raise AttributeError('Attribute %r not found\n%s\n%s\n' % (attr, classDict, bases))
    return default

class TestCaseMetaClass(type):
    # wrap each test method with
    # a) timeout check
    # b) totalrefcount check
    def __new__(meta, classname, bases, classDict):
        timeout = classDict.get('__timeout__', 'NONE')
        if timeout == 'NONE':
            timeout = getattr(bases[0], '__timeout__', None)
            if gettotalrefcount is not None and timeout is not None:
                timeout *= 6
        check_totalrefcount = _get_class_attr(classDict, bases, 'check_totalrefcount', True)
        error_fatal = _get_class_attr(classDict, bases, 'error_fatal', True)
        for key, value in classDict.items():
            if key.startswith('test') and callable(value):
                classDict.pop(key)
                #value = wrap_switch_count_check(value)
                value = wrap_timeout(timeout, value)
                my_error_fatal = getattr(value, 'error_fatal', None)
                if my_error_fatal is None:
                    my_error_fatal = error_fatal
                if my_error_fatal:
                    value = wrap_error_fatal(value)
                value = wrap_restore_handle_error(value)
                if check_totalrefcount:
                    value = wrap_refcount(value)
                classDict[key] = value
        return type.__new__(meta, classname, bases, classDict)

class TestCase(TestCaseMetaClass("NewBase", (BaseTestCase,), {})):
    __timeout__ = 1
    switch_expected = 'default'
    error_fatal = True

    def run(self, *args, **kwargs):
        if self.switch_expected == 'default':
            self.switch_expected = get_switch_expected(self.fullname)
        return BaseTestCase.run(self, *args, **kwargs)

    def tearDown(self):
        if getattr(self, 'skipTearDown', False):
            return
        if hasattr(self, 'cleanup'):
            self.cleanup()

    @property
    def testname(self):
        return getattr(self, '_testMethodName', '') or getattr(self, '_TestCase__testMethodName')

    @property
    def testcasename(self):
        return self.__class__.__name__ + '.' + self.testname

    @property
    def modulename(self):
        return os.path.basename(sys.modules[self.__class__.__module__].__file__).rsplit('.', 1)[0]

    @property
    def fullname(self):
        return splitext(basename(self.modulename))[0] + '.' + self.testcasename

    _none = (None, None, None)
    _error = _none

    def expect_one_error(self):
        assert self._error == self._none, self._error
        self._old_handle_error = gevent.get_hub().handle_error
        gevent.get_hub().handle_error = self._store_error

    def _store_error(self, where, type, value, tb):
        del tb
        if self._error != self._none:
            gevent.get_hub().parent.throw(type, value)
        else:
            self._error = (where, type, value)

    def peek_error(self):
        return self._error

    def get_error(self):
        try:
            return self._error
        finally:
            self._error = self._none

    def assert_error(self, type=None, value=None, error=None):
        if error is None:
            error = self.get_error()
        if type is not None:
            assert error[1] is type, error
        if value is not None:
            if isinstance(value, str):
                assert str(error[2]) == value, error
            else:
                assert error[2] is value, error
        return error
