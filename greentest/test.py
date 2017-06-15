'''
Created on Jun 29, 2011

@author: Sumit Khanna <sumit@penguindreams.org>
'''

import http.client
import time
from datetime import date, timedelta
import sys
import greentest
from greentest.condition import StatusSuccessCondition, WellFormedXMLSuccessCondition, HTMLResponseSuccessCondition,\
    NumberColumnsSuccessCondition, NumberRowsSuccessCondition, NumberXMLElementsSuccessCondition, MimeTypeSuccessCondition


class TestSet:

    # Display Color Codes
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAILRED = '\033[91m'
    ENDC = '\033[0m'

    # output levels
    LEVEL_ERROR = 10
    LEVEL_WARN = 20
    LEVEL_INFO = 30
    LEVEL_DEBUG = 40
    LEVEL_TRACE = 50

    # properties
    def __init__(self):
        self.tests = {}
        self.trace = False
        self.output_level = TestSet.LEVEL_INFO
        self.name = "Default Name"
        self.allPassed = True

    def set_on_fail(self, ret):
        if self.allPassed and ret is not None:
            self.allPassed = ret

    def run_tests(self):

        self.allPassed = True
        for test in self.tests:

            if isinstance(test, TestSet):
                print(self.OKBLUE + test.name + self.ENDC)
                test.trace = self.trace
                self.set_on_fail(test.run_tests())

            elif isinstance(test, AbstractTest):

                # parent Test
                if test.parentTest is not None:
                    if test.parentTest.resultTestStatus == AbstractTest.READY:
                        self.set_on_fail(test.parentTest.run_test())
                        self.write_test_results(test.parentTest.description, test.parentTest.resultTestMessage)

                # current Test
                self.set_on_fail(test.run_test())
                self.write_test_results(test.description, test.resultTestMessage)

            else:
                self.allPassed = False
                print("Unknown object in test set {0}".format(test))

        return self.allPassed

    def write_test_results(self, title, tuples):
        print("  " + self.HEADER + title + self.ENDC)
        for (status, message) in tuples:
            if status == AbstractTest.PASS:
                resp = self.OKBLUE + '[' + self.OKGREEN + '  ok  ' + self.OKBLUE + ']' + self.ENDC
            elif status == AbstractTest.FAIL:
                resp = self.OKBLUE + '[' + self.FAILRED + ' fail ' + self.OKBLUE + ']' + self.ENDC
            elif status == AbstractTest.TRACE and not self.trace:
                continue
            else:
                resp = self.OKBLUE + '[' + self.WARNING + '  !!  ' + self.OKBLUE + ']' + self.ENDC

            print('   ' + message.ljust(85) + resp)
            sys.stdout.flush()


class AbstractTest:

    # Check result Codes
    READY = -1
    PASS = 1
    FAIL = 0
    WARN = 3
    INFO = 4
    TRACE = 5

    def __init__(self):
        # properties
        self.description = 'ChangeMe: Default Abstract Description'
        self.requestType = 'GET'
        self.successConditions = []
        self.host = greentest.hostname
        self.port = greentest.port
        self.path = ''
        self.postData = None
        self.parentTest = None
        self.headers = {}
        self.generator = None
        self.couplers = None
        self.security = None

        # results
        self.resultBody = None
        self.resultStatus = None
        self.resultHeaders = None
        self.resultTestStatus = AbstractTest.READY
        self.resultTestMessage = []  # list of tuples [(PASS/FAIL,message)]

    def run_test(self):
        # 1) check parent test
        # 2) run couplers
        # 3) make request
        # 4) run checks

        if self.parentTest is not None and self.parentTest.resultTestStatus == AbstractTest.FAIL:
            self.resultTestMessage.append((AbstractTest.FAIL, '{0} (parent) Test Failed'.format(self.parentTest.description)))
            return False

        if self.couplers is not None:
            for c in self.couplers:
                c.couple_testers(self.parentTest, self)

        if self.generator is not None:
            self.postData = self.generator.generate_data()

        if self.security is not None:
            self.postData = self.security.process_data(self.postData)

        self.__make_request()
        for c in self.successConditions:
            if c.run_check(self):
                self.resultTestMessage.append((AbstractTest.PASS, 'Test {0} passed'.format(c.description)))
            else:
                self.resultTestMessage.append((AbstractTest.FAIL, 'Test {0} failed'.format(c.description)))
                return False

        self.resultTestStatus = AbstractTest.PASS
        return True

    def __make_request(self):
        connection = http.client.HTTPConnection(self.host, self.port)
        for name, value in self.headers:
            connection.putheader(name, value)
        connection.request(self.requestType, self.path, self.postData)
        result = connection.getresponse()
        self.resultStatus = result.getcode()
        self.resultBody = result.read()
        self.resultHeaders = result.getheaders()

        # Trace Debugg'in
        self.resultTestMessage.extend([
            (self.TRACE, 'Request: {0} {1}:{2}/{3}'.format(self.requestType, self.host, self.port, self.path)),
            (self.TRACE, 'Body: {0}'.format(self.postData)),
            (self.TRACE, 'Response Status: {0}'.format(self.resultStatus)),
        ])
        for hd, val in self.resultHeaders:
            self.resultTestMessage.extend([
                (self.TRACE, 'Response Header {0}: {1}'.format(hd, val)),
            ])
        self.resultTestMessage.extend([(self.TRACE, 'Response Body: {0}'.format(self.resultBody))])


class AbstractTimeQueryTest(AbstractTest):
    def __init__(self):
        self.stepHours = 1
        self.stepDays = 1
        self._path = ''
        AbstractTest.__init__(self)

    # %tsb - Unix Time Stamp Before  (now - stepHours, default to 1 hour)
    # %tsa - Unix Time Stamp After   (now + stepHours)
    # %db  - Date Before in YYYYMMDD (now - stepDays, default to 1 day)
    # %da  - Date After  in YYYYMMDD (now + stepDays)
    def _set_path(self, path):
        if path != '':  # Base constructor
            now = round(time.time() * 1000)
            t = path.replace('%tsb', str((now - 3600000) * int(self.stepHours)))
            t = t.replace('%tsa', str((now + 3600000) * int(self.stepHours)))
            t = t.replace('%db', (date.today() - timedelta(int(self.stepDays))).strftime('%Y%m%d'))
            t = t.replace('%da', (date.today() + timedelta(int(self.stepDays))).strftime('%Y%m%d'))
            self._path = t

    path = property(lambda self: self._path, _set_path)


class MultiFormatTestSet(TestSet):
    def __init__(self):
        TestSet.__init__(self)

        self.baseTest = None
        self.basePath = ''
        self.timeQueryPath = False
        self.stepHours = 1
        self.stepDays = 1

        # Formats
        self.tableHTMLSupported = True
        self.csvSupported = True
        self.tabSupported = True
        self.agraXMLSupported = False

        # Conversions
        self.unitsSupported = True
        self.timezoneSupported = True

        # Test Results
        self.numColumns = -1
        self.numRows = -1

    def _copy_base_test(self, extension):
        t = AbstractTimeQueryTest() if bool(self.timeQueryPath) else AbstractTest()
        t.host = self.baseTest.host
        t.port = self.baseTest.port
        t.stepHours = self.stepHours
        t.stepDays = self.stepDays

        if '?' in self.basePath:
            t.path = '.{}?'.format(extension).join(self.basePath.split('?'))
        else:
            t.path = '{}.{}'.format(self.basePath, extension)

        t.description = '{0} [{1}]'.format(self.name, extension)
        ok = StatusSuccessCondition()
        ok.code = 200
        ok.status = 'OK'
        t.successConditions.append(ok)
        return t

    def add_conversions(self, test, type):
        """Takes a single Abstract Test and returns a list of tests for
    specific conversions based on the unitsSupported and timezoneSupported
    members. Type should be csv,txt.
    Returned list does include original test"""
        if bool(self.unitsSupported):
            pass
        if bool(self.timezoneSupported):
            pass

    def _add_mime(self, mime, test):
        ms = MimeTypeSuccessCondition()
        ms.mimeType = mime
        test.successConditions.append(ms)

    def run_tests(self):

        self.tests = []

        if bool(self.tableHTMLSupported):
            t = self._copy_base_test('table.html')
            self._add_mime('text/html', t)
            t.successConditions.append(HTMLResponseSuccessCondition())
            self.tests.append(t)
        if bool(self.csvSupported):
            t = self._copy_base_test('csv')
            self._add_mime('text/csv', t)
            c = NumberColumnsSuccessCondition()
            c.delimiter = 'comma'
            c.numColumns = self.numColumns
            r = NumberRowsSuccessCondition()
            r.numRows = self.numRows
            r.header = True
            if int(self.numRows) != -1:
                t.successConditions.append(r)
            if int(self.numColumns) != -1:
                t.successConditions.append(c)
            self.tests.append(t)
        if bool(self.tabSupported):
            t = self._copy_base_test('txt')
            self._add_mime('text/tab-separated-values', t)
            c = NumberColumnsSuccessCondition()
            c.delimiter = 'tab'
            c.numColumns = self.numColumns
            r = NumberRowsSuccessCondition()
            r.numRows = self.numRows
            r.header = True
            if int(self.numRows) != -1:
                t.successConditions.append(r)
            if int(self.numColumns) != -1:
                t.successConditions.append(c)
            self.tests.append(t)
        if bool(self.agraXMLSupported):
            t = self._copy_base_test('sense.xml')
            t.successConditions.append(WellFormedXMLSuccessCondition())
            self.tests.append(t)

        TestSet.run_tests(self)
