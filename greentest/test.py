'''
Created on Jun 29, 2011

@author: Sumit Khanna <sumit@penguindreams.org>
'''

import http.client
         
class TestSet:         
            
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
  def __init__(self):
    self.tests = {}
    self.trace = False
    self.output_level = TestSet.LEVEL_INFO  

  def run_tests(self):
    for test in self.tests:
      test.run_test()
      self.write_test_results(test.description,test.resultTestMessage)

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

  def __init__(self):
    #properties 
    self.description = 'ChangeMe: Default Abstract Description'
    self.requestType = 'GET'
    self.successConditions = []
    self.host = None
    self.port = 80
    self.path = ''
    self.postData = None
    self.parentTest = None
    self.headers = {}
    self.generator = None
    
    #results
    self.resultBody = None
    self.resultStatus = None
    self.resultHeaders = None
    self.resultTestStatus = AbstractTest.READY  
    self.resultTestMessage = [] #list of tuples [(PASS/FAIL,message)]
  
  
  def run_test(self):
    #1) run parent if necessary
    #2) run couplers 
    #3) make request
    #4) run checks
    if self.parentTest != None:
      if self.parentTest.resultTestStatus == AbstractTest.READY:
        print("Running Parent Tests")
        self.parentTest.run_test()
      if self.parentTest.resultTestStatus == AbstractTest.FAIL:
        self.resultTestMessage.append( (AbstractTest.FAIL,'{0} (parent) Test Failed'.format(self.parentTest.description)) )
        return False
      if self.parentTest.resultTestStatus == AbstractTest.PASS:
        if self.generator != None:
          self.generator.set_result_infomration(self.parentTest.resultStatus, self.parentTest.resultHeaders, self.parentTest.resultBody)

    if self.generator != None:
      self.postData = self.generator.generate_data() 
       
    self.__make_request()
    for c in self.successConditions:
      if c.run_check(self):
        self.resultTestMessage.append( (AbstractTest.PASS , 'Test {0} passed'.format(c.description)) )
      else:
        self.resultTestMessage.append( (AbstractTest.FAIL, 'Test {0} failed'.format(c.description)) )
        return False
    
    self.resultTestStatus = AbstractTest.PASS
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
    ])
    for hd,val in self.resultHeaders:
      self.resultTestMessage.extend([
        (self.TRACE,'Response Header {0}: {1}'.format(hd,val)),                                     
    ])    
    self.resultTestMessage.extend([
      (self.TRACE,'Response Body: {0}'.format(self.resultBody))
    ])                               
  
  

