#!/usr/bin/env python3
import configparser
import logging
import os
import glob
import ast

config = configparser.RawConfigParser()
# remove case insensitivity
config.optionxform = lambda option: option

# Object Cache
loader_classes = {}


# Taken from
# http://stackoverflow.com/questions/547829/how-to-dynamically-load-a-python-class
def load_obj(name):
    components = name.split('.')
    path = '.'.join(components[:-1])
    clss = components[-1:][0]
    mod = __import__(path, globals(), locals(), clss)
    return getattr(mod, clss)()


def load_config():
    config.read(glob.glob(os.path.join('config/', '*.config')))


def set_args(object, key, value):
    arg = None
    if '\\' in value:
        (optype, opt) = value.split('\\')
        if optype == 'class-ref':
            if opt.startswith('{'):
                arg = []
                for c in opt.strip('{}').split(','):
                    arg.append(get_class(c))
            else:
                arg = get_class(opt)
    else:
        if value.startswith('{'):
            arg = ast.literal_eval(value)
        else:
            arg = value

    logging.debug('Setting attribute {0} to {1} for class {2}'.format(key, arg, object))
    setattr(object, key, arg)


def get_class_name(bean):
    if not config.has_option(bean, 'inherit'):
        return config.get(bean, 'class')
    if config.has_option(bean, 'class'):
        return config.get(bean, 'class')
    return get_class_name(config.get(bean, 'inherit'))


def get_class(idu):
    if idu in loader_classes:
        logging.debug('Loading Cached Object ' + idu)
        return loader_classes[idu]

    bean = config.items(idu)
    name = get_class_name(idu)

    obj = load_obj(name)
    logging.debug('Created Object {0} of type {1}'.format(idu, name))

    # inherited
    #  to do this correctly we really want to roll up
    #  and not down. This works for now.
    cur = idu
    while (config.has_option(cur, 'inherit')):
        cur = config.get(cur, 'inherit')
        for (skey, svalue) in config.items(cur):
            if skey != 'class' and skey != 'inherit':
                set_args(obj, skey, svalue)

    for (key, value) in bean:
        if key == 'class' or key == 'inherit':
            continue
        else:
            set_args(obj, key, value)

    loader_classes[idu] = obj
    return obj
