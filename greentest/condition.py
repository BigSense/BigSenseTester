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

class OKSuccessCondition(AbstractSuccessCondition):
  
  description = '200 Success'
  
  def run_check(self,test : AbstractTest):
    return test.resultStatus == http.client.OK