'''
Created on Jul 18, 2011

@author: khannast
'''
from xml.dom.minidom import Document
import time


class AbstractGenerator:
  
  def __init__(self):
    pass
  
  def set_result_infomration(self, status, headers, body):
    self._status = status
    self._headers = headers
    self._body = body
  
  def generate_data(self):
    return "Unimplemented"


class GreenXMLDataGenerator(AbstractGenerator):
  
  def __init__(self):
    AbstractGenerator.__init__(self)
    self.numPackages = 1
  
  def generate_data(self):
    doc = Document()
    root = doc.createElement('GreenData')

    for i in range(int(self.numPackages)):
      pack = doc.createElement('package')

      #We want time as a long as number of milisecongs
      pack.setAttribute("timestamp", str(round(time.time()* 1000)))
      pack.setAttribute("timezone", "UTC")
      pack.setAttribute("id","00:11:22:33:44:55:66")
  
      sens = doc.createElement('sensors')
  
      sensors = [{'id':'AGEWA99B','type':'Temperature','units':'C','data':'34'},
                 {'id':'AGEWA45C','type':'Temperature','units':'C','data':'36'},
                 {'id':'DFERWE9F','type':'Temperature','units':'C','data':'30'}]
      for s in sensors:
        senNode = doc.createElement('sensor')
        senNode.setAttribute('id',s['id'])
        senNode.setAttribute('type',s['type'])
        senNode.setAttribute('units',s['units'])
        
        ddata = doc.createElement('data')
        ddata.appendChild(doc.createTextNode(s['data']))
  
        senNode.appendChild(ddata)
        sens.appendChild(senNode)

      pack.appendChild(sens)
      root.appendChild(pack)
    
    doc.appendChild(root)
    return doc.toprettyxml(indent=' ')