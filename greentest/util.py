#!/usr/bin/env python


def to_camel_case(word):
    return ''.join(word.title().split('_'))
