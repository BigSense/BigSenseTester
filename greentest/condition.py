'''
Created on Jul 5, 2011

@author: khannast
'''
import http.client
from greentest.test import AbstractTest

class AbstractSuccessCondition:
  
  description = 'Unimplemented'
  
  def run_check(self,test : AbstractTest):
    
    return False

class StatusSuccessCondition(AbstractSuccessCondition):
  
  description = property(lambda self: 'Status {0} {1}'.format(self.code, self.status) )
  code = -1
  status = 'Unimplemented'
  
  def run_check(self,test : AbstractTest):
    return test.resultStatus == self.code
  
class HeaderSuccessCondition(AbstractSuccessCondition):
  
  description = property(lambda self: 'Header {0} (min/max: {1}/{2}'.format(self.header,self.min,self.max))
  header = None
  min = 1
  max = 1
  
  def run_check(self, test : AbstractTest):
    
    if self.header == None:
      return False
    
    count = 0
    for h in test.resultHeaders:
      if h == self.header:
        count += 1
    return count > min and count < max
  
  
  