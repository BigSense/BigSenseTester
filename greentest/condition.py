'''
Created on Jul 5, 2011

@author: khannast
'''
from xml.sax.handler import ContentHandler
from xml.sax import parseString
from xml.sax._exceptions import SAXParseException
from xml.etree import ElementTree
from html.parser import HTMLParser, HTMLParseError
import six
import json


class AbstractSuccessCondition:

    description = "Unimplemented"

    def __init__(self):
        pass

    def run_check(self, test):
        return False


class StatusSuccessCondition(AbstractSuccessCondition):

    description = property(lambda self: 'Status {0} {1}'.format(self.code, self.status))

    def __init__(self):
        AbstractSuccessCondition.__init__(self)
        self.code = -1
        self.status = 'Unimplemented'

    def run_check(self, test):
        return int(test.resultStatus) == int(self.code)


class NumberColumnsSuccessCondition(AbstractSuccessCondition):

    description = property(lambda self: 'Number of columns {0} (Delimiter: {1})'.format(self.numColumns, self.delimiter))

    def __init__(self):
        AbstractSuccessCondition.__init__(self)
        self.numColumns = -1
        self.delimiter = ' '

    def run_check(self, test):
        rows = str(test.resultBody, encoding='utf8').split('\n')
        dell = ' '
        if self.delimiter == 'tab':
            dell = '\t'
        elif self.delimiter == 'comma':
            dell = ','
        for r in rows:
            if r.strip() != '':
                if (len(r.split(dell)) != int(self.numColumns)):
                    return False
        return True


class ValidJSONSuccessCondition(AbstractSuccessCondition):

    description = "Valid JSON"

    def __init__(self):
        AbstractSuccessCondition.__init__(self)

    def run_check(self, test):
        try:
            json_object = json.loads(test.resultBody.decode('UTF-8'), ContentHandler())
            return True
        except ValueError:
            return False


class WellFormedXMLSuccessCondition(AbstractSuccessCondition):

    description = "Well Formed XML"

    def __init__(self):
        AbstractSuccessCondition.__init__(self)

    def run_check(self, test):
        try:
            parseString(test.resultBody, ContentHandler())
            return True
        except SAXParseException:
            return False


class HTMLResponseSuccessCondition(AbstractSuccessCondition):

    description = "HTML Response"

    def __init__(self):
        AbstractSuccessCondition.__init__(self)

    def run_check(self, test):
        try:
            p = HTMLParser()
            p.feed(str(test.resultBody))
            p.close()
            return True
        except HTMLParseError:
            return False


class NumberXMLElementsSuccessCondition(AbstractSuccessCondition):

    description = property(lambda self: 'Search XPath {0} / Number of Elements {1}'.format(self.searchXPath, self.numElements))

    def __init__(self):
        AbstractSuccessCondition.__init__(self)
        self.searchXPath = './/'
        self.numElements = 0

    def run_check(self, test):
        try:
            return len(ElementTree.fromstring(test.resultBody).findall(self.searchXPath)) == int(self.numElements)
        except ElementTree.ParseError:
            return False


class FieldValueSuccessCondition(AbstractSuccessCondition):

    description = property(lambda self: '{0} Field {1} is "{2}" for all rows'.format(self._fmt_delimiter(), self.field, self.value))

    def __init__(self):
        AbstractSuccessCondition.__init__(self)
        self.field = 'Unimplemented'
        self.value = ''
        self._delimiter = '\t'

    def _str_to_delimiter(self, v):
        if v.strip().lower() == 'tab':
            self._delimiter = '\t'
        elif v.strip().lower() == 'comma':
            self._delimiter = ','
        else:
            self._delimiter = v.strip().lower()

    def _fmt_delimiter(self):
        if self._delimiter == '\t':
            return 'Tab Delimited'
        if self._delimiter == ',':
            return 'Comma Delimited'
        return self._delimiter

    delimiter = property(_fmt_delimiter, _str_to_delimiter)

    def run_check(self, test):
        body = str(test.resultBody, encoding='utf8').split('\n')
        headers = body[:1][0].split(self._delimiter)
        for row in body[1:]:
            if row.strip() != '':
                result = row.split(self._delimiter)[headers.index(self.field)]
                if result == '' and self.value == '':
                    return True
                if float(result) != float(self.value):
                    return False
        return True


class BodyTextSuccessCondition(AbstractSuccessCondition):

    description = property(lambda self: 'Search Body Text [{0}]: "{1}"'.format('present' if self._present() else 'absent', self.searchText))

    def __init__(self):
        AbstractSuccessCondition.__init__(self)
        self.searchText = ''
        self.present = True

    def run_check(self, test):
        search = self.searchText
        body = str(test.resultBody, encoding='utf8')

        return search in body if self._present() else search not in body

    def _present(self):
        if isinstance(self.present, six.string_types) and self.present.lower() == 'false':
            return False
        return True


class MimeTypeSuccessCondition(AbstractSuccessCondition):

    description = property(lambda self: "ContentType: {0}".format(self.mimeType))

    def __init__(self):
        AbstractSuccessCondition.__init__(self)
        self.mimeType = 'text/plain'

    def run_check(self, test):
        for hd, val in test.resultHeaders:
            if hd == 'Content-Type' and val == self.mimeType:
                return True
        return False


class NumberRowsSuccessCondition(AbstractSuccessCondition):

    description = property(lambda self: 'Number of Rows: {0} / Skip Header: {1}'.format(self.numRows, self.header))

    def __init__(self):
        AbstractSuccessCondition.__init__(self)
        self.numRows = -1
        self.header = False

    def run_check(self, test):
        rows = str(test.resultBody, encoding='utf8').split('\n')
        count = 0
        for r in rows:
            if r.strip() != '':
                count += 1

        if bool(self.header) is True:
            return count - 1 == int(self.numRows)
        else:
            return count == int(self.numRows)


class HeaderSuccessCondition(AbstractSuccessCondition):

    description = property(lambda self: 'Header {0} (min/max: {1}/{2})'.format(self.header, self.min, self.max))

    def __init__(self):
        AbstractSuccessCondition.__init__(self)
        self.header = None
        self.min = 1
        self.max = 1

    def run_check(self, test):

        if self.header is None:
            return False

        count = 0
        for hd, val in test.resultHeaders:
            if hd == self.header:
                count += 1
        return count >= int(self.min) and count <= int(self.max)
