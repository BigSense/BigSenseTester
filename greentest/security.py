import rsa
import base64
__author__ = 'Sumit Khanna <sumit@penguindreams.org>'


class AbstractSecurityManager(object):
    def __init__(self):
        pass

    def process_data(self, data):
        return data


class DisabledSecurityManager(AbstractSecurityManager):
    def process_data(self, data):
        return AbstractSecurityManager.process_data(self, data)


class SignatureSecurityManager(AbstractSecurityManager):
    def __init__(self):
        self._keyFile = None
        self._key = None

    def _load_key_file(self, file):
        self._keyFile = file
        with open(file, 'rb') as file:
            keydata = file.read()
        self._key = rsa.PrivateKey.load_pkcs1(keydata)

    def process_data(self, data):
        if data is None or data == '':
            return data
        signature = base64.b64encode(rsa.sign(data.encode('utf-8'), self._key, 'SHA-1')).decode("utf-8")
        return "{0}\n\n{1}".format(data, signature)

    keyFile = property(lambda self: self._keyFile, lambda self, value: self._load_key_file(value))
