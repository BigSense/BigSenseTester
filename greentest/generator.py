'''
Created on Jul 18, 2011

@author: khannast
'''
from xml.dom.minidom import Document
import time
import base64
import json


class AbstractGenerator:

  def __init__(self):
    pass

  def set_result_infomration(self, status, headers, body):
    self._status = status
    self._headers = headers
    self._body = body

  def generate_data(self):
    return "Unimplemented"

  def _loc_not_empty(self, ele):
    return ele in self.location and self.location[ele] != ''

  def _location(self, ele):
    return str(self.location[ele]) if ele in self.location else ''


class RegistrationDataGenerator(AbstractGenerator):

  def __init__(self):
    AbstractGenerator.__init__(self)

  def generate_date(self):
    doc = Document()
    root = doc.createElement('AltaRegister')

    doc.appendChild(root)
    return doc.toprettyxml(indent=' ')


class JSONDataGenerator(AbstractGenerator):

  def __init__(self):
    AbstractGenerator.__init__(self)
    self.numPackages = 1
    self.sensors = []
    self.name = "FunctionalTester"
    self.location = None

  def generate_data(self):

    packages = []
    for i in range(int(self.numPackages)):
        data = {'id': self.name,
                'timestamp': '{0}'.format(round(time.time()* 1000)) }

        if self.location:
          data['gps'] = {}

          if self._loc_not_empty('longitude') or self._loc_not_empty('latitude') or self._loc_not_empty('altitude'):
            data['gps']['location'] = {}
            data['gps']['location']['longitude'] = float(self._location('longitude'))
            data['gps']['location']['latitude'] = float(self._location('latitude'))
            data['gps']['location']['altitude'] = float(self._location('altitude'))

          if self._loc_not_empty('speed') or self._loc_not_empty('track') or self._loc_not_empty('climb'):
            data['gps']['delta'] = {}
            data['gps']['delta']['speed'] = float(self._location('speed'))
            data['gps']['delta']['track'] = float(self._location('track'))
            data['gps']['delta']['climb'] = float(self._location('climb'))

          if self._loc_not_empty('longitude_error') or self._loc_not_empty('latitude_error') or self._loc_not_empty('altitude_error') or self._loc_not_empty('speed_error') or self._loc_not_empty('track_error') or self._loc_not_empty('climb_error'):
            data['gps']['accuracy'] = {}
            data['gps']['accuracy']['longitude_error'] = float(self._location('longitude_error'))
            data['gps']['accuracy']['latitude_error'] = float(self._location('latitude_error'))
            data['gps']['accuracy']['altitude_error'] = float(self._location('altitude_error'))
            data['gps']['accuracy']['speed_error'] = float(self._location('speed_error'))
            data['gps']['accuracy']['climb_error'] = float(self._location('climb_error'))
            data['gps']['accuracy']['track_error'] = float(self._location('track_error'))

        data['sensors'] = []
        for s in self.sensors:
            data['sensors'].append({'id': s.id,
                                    'type': s.type,
                                    'units': s.units,
                                    'data': s.data})
        packages.append(data)

    return json.dumps(packages)


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
        gps = doc.createElement('gps')

        if self._loc_not_empty('longitude') or self._loc_not_empty('latitude') or self._loc_not_empty('altitude'):
          loc = doc.createElement('location')
          loc.setAttribute('longitude', self._location('longitude'))
          loc.setAttribute('latitude', self._location('latitude'))
          loc.setAttribute('altitude', self._location('altitude'))
          gps.appendChild(loc)

        if self._loc_not_empty('speed') or self._loc_not_empty('track') or self._loc_not_empty('climb'):
          delta = doc.createElement('delta')
          delta.setAttribute('speed', self._location('speed'))
          delta.setAttribute('track', self._location('track'))
          delta.setAttribute('climb', self._location('climb'))
          gps.appendChild(delta)

        if self._loc_not_empty('longitude_error') or self._loc_not_empty('latitude_error') or self._loc_not_empty('altitude_error') or self._loc_not_empty('speed_error') or self._loc_not_empty('track_error') or self._loc_not_empty('climb_error'):
            acc = doc.createElement('accuracy')
            acc.setAttribute('longitude_error', self._location('longitude_error'))
            acc.setAttribute('latitude_error', self._location('latitude_error'))
            acc.setAttribute('altitude_error', self._location('altitude_error'))
            acc.setAttribute('speed_error', self._location('speed_error'))
            acc.setAttribute('climb_error', self._location('climb_error'))
            acc.setAttribute('track_error', self._location('track_error'))
            gps.appendChild(acc)

        pack.appendChild(gps)

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
    self.name = "BigSenseTester"
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
