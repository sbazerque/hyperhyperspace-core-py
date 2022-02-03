import base64
import hashlib

class RMD:
    def rmd160base64(self, text):
        h = hashlib.new('rmd160')
        h.update(text.encode('utf-8'))
        return base64.b64encode(h.digest()).decode('utf-8')
        
    def rmd160hex(self, text):
        h = hashlib.new('rmd160')
        h.update(text.encode('utf-8'))
        return h.hexdigest()

class SHA:

    def shaBase64(self, algo, text):
        h = hashlib.new(algo)
        h.update(text.encode('utf-8'))
        return base64.b64encode(h.digest()).decode('utf-8')

    def sha1base64(self, text):
        return self.shaBase64('sha1', text)

    def sha256base64(self, text):
        return self.shaBase64('sha256', text)

    def sha512base64(self, text):
        return self.shaBase64('sha512', text)


    def shaHex(self, algo, text):
        h = hashlib.new(algo)
        h.update(text.encode('utf-8'))
        return h.hexdigest()

    def sha1hex(self, text):
        return self.shaHex('sha1', text)

    def sha256hex(self, text):
        return self.shaHex('sha256', text)

    def sha512hex(self, text):
        return self.shaHex('sha512', text)

