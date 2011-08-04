'''
Created on Jul 5, 2011

@author: khannast
'''
from greentest.test import AbstractTest

class AbstractSuccessCondition:
  
  description = "Unimplemented"
  
  def __init__(self):
    pass
  
  def run_check(self,test : AbstractTest):    
    return False

class StatusSuccessCondition(AbstractSuccessCondition):
  
  description = property(lambda self: 'Status {0} {1}'.format(self.code, self.status) )
  
  def __init__(self):
    AbstractSuccessCondition.__init__(self)    
    self.code = -1
    self.status = 'Unimplemented'
  
  def run_check(self,test : AbstractTest):
    return int(test.resultStatus) == int(self.code)
  
class HeaderSuccessCondition(AbstractSuccessCondition):
  
  description = property(lambda self: 'Header {0} (min/max: {1}/{2})'.format(self.header,self.min,self.max))
  
  def __init__(self):
    AbstractSuccessCondition.__init__(self)    
    self.header = None
    self.min = 1
    self.max = 1
  
  def run_check(self, test : AbstractTest):
    
    if self.header == None:
      return False
    
    count = 0
    for hd,val in test.resultHeaders:
      if hd == self.header:
        count += 1
    return count >= int(self.min) and count <= int(self.max)
  
  
  