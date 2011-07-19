'''
Created on Jun 29, 2011

@author: Sumit Khanna <sumit@penguindreams.org>
'''

import http.client
         
class TestSet:
  
  #properties
  tests = {}
  trace = False
    
  def run_tests(self):
    for test in self.tests:
      test.run_test()
      self.write_test_results(test.description,test.resultTestMessage)         
            
  #Display Color Codes
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAILRED = '\033[91m'
  ENDC = '\033[0m'
  
  #output levels
  LEVEL_ERROR = 10
  LEVEL_WARN  = 20
  LEVEL_INFO  = 30
  LEVEL_DEBUG = 40
  LEVEL_TRACE = 50
  
  #properties
  output_level = LEVEL_INFO 

  def write_test_results(self,title,tuples):
    print(self.HEADER + title + self.ENDC)
    for (status,message) in tuples:
      if status == AbstractTest.PASS:
        resp = self.OKBLUE + '[' + self.OKGREEN + '  ok  ' + self.OKBLUE + ']' + self.ENDC
      elif status == AbstractTest.FAIL:
        resp = self.OKBLUE + '[' + self.FAILRED  + ' fail ' + self.OKBLUE + ']' + self.ENDC
      elif status == AbstractTest.TRACE and not self.trace:
        continue
      else:
        resp = self.OKBLUE + '[' + self.WARNING  + '  !!  ' + self.OKBLUE + ']' + self.ENDC
        
      print('   ' + message.ljust(85) + resp)

              

class AbstractTest:

  #Check result Codes
  READY = -1
  PASS  = 1
  FAIL  = 0
  WARN  = 3
  INFO  = 4
  TRACE = 5

  #properties 
  description = 'ChangeMe: Default Abstract Description'
  requestType = 'GET'
  successConditions = []
  host = None
  port = 80
  path = ''
  postData = None
  parentTest = None
  headers = {}
  generator = None
  
  #results
  resultBody = None
  resultStatus = None
  resultHeaders = None
  resultTestStatus = READY  
  resultTestMessage = [] #list of tuples [(PASS/FAIL,message)]

  
  def run_test(self):
    #1) run parent if necessary
    #2) run couplers 
    #3) make request
    #4) run checks
    
    if self.parentTest != None:
      if self.parentTest.resultTestStatus == self.READY:
        self.parentTest.run_test()
      if self.parentTest.resultTestStatus == self.FAIL:
        self.resultTestMessage.append( (self.FAIL,'{0} (parent) Test Failed'.format(self.parentTest.description)) )
        return False
      if self.parentTest.resultTestStatus == self.PASS:
        if self.generator != None:
          self.generator.set_result_infomration(self.parentTest.resultStatus, self.parentTest.resultHeaders, self.parentTest.resultBody)

    if self.generator != None:
      self.postData = self.generator.generate_data() 
      
    self.__make_request()
    for c in self.successConditions:
      if c.run_check(self):
        self.resultTestMessage.append( (self.PASS , 'Test {0} passed'.format(c.description)) )
      else:
        self.resultTestMessage.append( (self.FAIL, 'Test {0} failed'.format(c.description)) )
        return False
    
    return True  
      
  
  def __make_request(self):       
    connection = http.client.HTTPConnection(self.host,self.port)
    for name,value in self.headers:
      connection.putheader(name,value)    
    connection.request(self.requestType,self.path,self.postData)
    result = connection.getresponse()
    self.resultStatus = result.getcode()
    self.resultBody = result.read()
    self.resultHeaders = result.getheaders()
    
    #Trace Debugg'in
    self.resultTestMessage.extend([
      (self.TRACE,'Request: {0} {1}:{2}/{3}'.format(self.requestType,self.host,self.port,self.path)),
      (self.TRACE,'Body: {0}'.format(self.postData)),
      (self.TRACE,'Response Status: {0}'.format(self.resultStatus)),
      (self.TRACE,'Response Body: {0}'.format(self.resultBody))                             
    ])    
  
  
  

