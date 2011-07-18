'''
Created on Jul 18, 2011

@author: khannast
'''
from xml.dom.minidom import Document
import time


class AbstractGenerator:
  
  def set_result_infomration(self, status, headers, body):
    self._status = status
    self._headers = headers
    self._body = body
  
  def generate_data(self):
    return "Unimplemented"


class GreenXMLDataGenerator(AbstractGenerator):
  
  def generate_data(self):
    doc = Document()
    root = doc.createElement('GreenData')

    ts = doc.createElement('timestamp')
    ts.setAttribute('zone','UTC')
    ts.appendChild(doc.createTextNode(str(time.time())))

    sens = doc.createElement('Sensors')

    sensors = [{'id':'AGEWA99B','type':'Temperature','units':'C','data':'34'},
               {'id':'AGEWA45C','type':'Temperature','units':'C','data':'36'},
               {'id':'DFERWE9F','type':'Temperature','units':'C','data':'30'}]
    for s in sensors:
      senNode = doc.createElement('Sensor')

      did = doc.createElement('id')
      dtype = doc.createElement('type')
      dunits = doc.createElement('units')
      ddata = doc.createElement('data')

      did.appendChild(doc.createTextNode(s['id']()))
      dtype.appendChild(doc.createTextNode(s['type']))
      dunits.appendChild(doc.createTextNode(s['units']))
      ddata.appendChild(doc.createTextNode(s['data']))
 
      senNode.appendChild(did)
      senNode.appendChild(dtype)
      senNode.appendChild(dunits)
      senNode.appendChild(ddata)
      sens.appendChild(senNode)

    root.appendChild(ts)
    root.appendChild(sens)
    doc.appendChild(root)
    return doc.toprettyxml(indent=' ')