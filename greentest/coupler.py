'''
Created on Oct 19, 2011

@author: khannast
'''
from urllib.parse import urlparse
from greentest.test import AbstractTest

class AbstractCoupler(object):
  
  def __init__(self):
    object.__init__(self)
    
  def couple_testers(self,prev : AbstractTest, next: AbstractTest):
    pass
    

class PostToGetCoupler(AbstractCoupler):
  
  def __init__(self):
    AbstractCoupler.__init__(self)
    self.locationHeader = 1
    self.format = None
    
  def couple_testers(self,prev : AbstractTest, next: AbstractTest):
    count = 1
    for h,v in prev.resultHeaders:
      if h == 'Location':
        if int(self.locationHeader) == count:
          next.path = urlparse(v).path
          if self.format != None:
            next.path = next.path.split('.')[0] + '.' + self.format
        else:
          count += 1