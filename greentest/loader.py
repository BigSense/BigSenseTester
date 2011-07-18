#!/usr/bin/env python3
import configparser
import logging

loader_config = configparser.RawConfigParser()
#remove case insensitivity 
loader_config.optionxform = lambda option: option

loader_classes = {}

#Taken from
# http://stackoverflow.com/questions/547829/how-to-dynamically-load-a-python-class
def load_obj(name):
    components = name.split('.')
    path = '.'.join(components[:-1])
    clss = components[-1:][0]
    mod = __import__(path,globals(),locals(),clss)
    return getattr(mod,clss)()

def load_config(configFile):
    loader_config.readfp(open(configFile,'r'))

def get_class(idu):
  if idu in loader_classes:
    logging.debug('Loading Cached Object ' + idu)
    return loader_classes[idu]

  bean = loader_config.items(idu)
  name = loader_config.get(idu,'class')
  obj = load_obj(name)
  logging.debug('Created Object {0}'.format(name))
  for (key,value) in bean:
    if key == 'class':
      continue
    else:
      arg = None
      if '\\' in value:
        (optype,opt) = value.split('\\')
        if optype == 'class-ref':
          if opt.startswith('{'):
            arg = []
            for c in opt.strip('{}').split(','):
              arg.append(get_class(c))
          else:            
            arg = get_class(opt)
      else:
        arg = value

      logging.debug('Setting attribute {0} to {1} for class {2}'.format(key,arg,obj))
      setattr(obj,key,arg)

  return obj
