'''
Created on Oct 19, 2011

@author: khannast
'''
from urllib.parse import urlparse
from greentest.test import AbstractTest
from greentest.util import to_camel_case
from greentest.condition import FieldValueSuccessCondition


class AbstractCoupler(object):
    def __init__(self):
        object.__init__(self)

    def couple_testers(self, prev: AbstractTest, next: AbstractTest):
        pass


class LocationPostToGetCoupler(AbstractCoupler):
    def __init__(self):
        AbstractCoupler.__init__(self)

    def couple_testers(self, prev: AbstractTest, next: AbstractTest):
        fields = ['latitude', 'longitude', 'altitude', 'speed', 'climb', 'track', 'latitude_error', 'longitude_error', 'altitude_error', 'speed_error', 'climb_error', 'track_error']
        conditions = []
        for f in fields:
            cond = FieldValueSuccessCondition()
            cond.field = to_camel_case(f)
            cond.value = prev.generator.location[f] if f in prev.generator.location else ''
            cond.delimiter = 'tab'
            conditions.append(cond)

        next.successConditions = conditions
        next.requestType = 'GET'
        next.path = "/Query/Latest/100.txt?RelayID={}".format(prev.generator.name)


class PostToGetCoupler(AbstractCoupler):
    def __init__(self):
        AbstractCoupler.__init__(self)
        self.locationHeader = 1
        self.format = None

    def couple_testers(self, prev: AbstractTest, next: AbstractTest):
        count = 1
        for h, v in prev.resultHeaders:
            if h == 'Location':
                if int(self.locationHeader) == count:
                    next.path = urlparse(v).path
                    if self.format is not None:
                        next.path = next.path.split('.')[0] + '.' + self.format
                else:
                    count += 1
