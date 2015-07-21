'''
Created on Jul 18, 2011

@author: khannast
'''
from xml.dom.minidom import Document
import time
import base64


class AbstractGenerator:
  
  def __init__(self):
    pass
  
  def set_result_infomration(self, status, headers, body):
    self._status = status
    self._headers = headers
    self._body = body
  
  def generate_data(self):
    return "Unimplemented"

class RegistrationDataGenerator(AbstractGenerator):
  
  def __init__(self):
    AbstractGenerator.__init__(self)
    
  def generate_date(self):
    doc = Document()
    root = doc.createElement('AltaRegister')
    
    doc.appendChild(root)
    return doc.toprettyxml(indent=' ')
    

class XMLDataGenerator(AbstractGenerator):
  
  def __init__(self):
    AbstractGenerator.__init__(self)
    self.numPackages = 1
    self.sensors = []
    self.name = "FunctionalTester"
    self.location = None
  
  def generate_data(self):
    """Creates Sense XML. Location None or {x, y, accuracy, altitude}"""
    doc = Document()
    root = doc.createElement('sensedata')

    for i in range(int(self.numPackages)):
      pack = doc.createElement('package')

      #We want time as a long as number of milisecongs
      pack.setAttribute("timestamp", '{0}'.format(round(time.time()* 1000)))
      pack.setAttribute("id",self.name)

      if self.location:
        loc = doc.createElement('location')
        loc.setAttribute('longitude', str(self.location['longitude']))
        loc.setAttribute('latitude', str(self.location['latitude']))
        loc.setAttribute('accuracy', str(self.location['accuracy']))
        loc.setAttribute('altitude', str(self.location['altitude']))
        pack.appendChild(loc)
  
      sens = doc.createElement('sensors')
  
      for s in self.sensors:
        senNode = doc.createElement('sensor')
        if s['id'] != '':
          senNode.setAttribute('id',s['id'])
        senNode.setAttribute('type',s['type'])
        senNode.setAttribute('units',s['units'])
        senNode.setAttribute('timestamp',str(round(time.time()*1000)))
        
        ddata = doc.createElement('data')
        ddata.appendChild(doc.createTextNode(s['data']))
  
        senNode.appendChild(ddata)
        sens.appendChild(senNode)

      pack.appendChild(sens)
      root.appendChild(pack)
    
    doc.appendChild(root)
    return doc.toxml()
  
class OneWireXMLDataGenerator(XMLDataGenerator):
  
  def __init__(self):
    XMLDataGenerator.__init__(self)     
    self.name = "OneWireTester"
    self.sensors = [{'id':'AGEWA99B','type':'Temperature','units':'C','data':'34'},
        {'id':'WTR001AD-V','type':'Volume','units':'ml','data':'50'},
        {'id':'WTR001AD-FR','type':'FlowRate','units':'ml/s','data':'2.45'}]


class PhotoXMLDataGenerator(XMLDataGenerator):
  
  def __init__(self):
    XMLDataGenerator.__init__(self)
    self.name = 'PhotoTester'
    self.id = ''
    self.photoFile = None
    
  def generate_data(self):
    fd = open(self.photoFile,'rb')
    image = fd.read()
    fd.close()
    encodedImage = base64.encodebytes(image).decode("utf-8")
    self.sensors = [{'id':self.id,'type':'Photo','units':'NPhotoU','data':encodedImage}]
    return XMLDataGenerator.generate_data(self)    