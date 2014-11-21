#!/usr/bin/env python2
# -*- coding: utf-8 -*-
__author__ = "David Bidner, Rene Höbling and Alexander Wachter"
__license__ = "BSD 2-Clause"
__version__ = "rolling"
__status__ = "Demo"

# Provides a more or less complex structure for the SMM Network server

import rsa
import os.path
import time
import stomp
import json
import base64
import random
import sys
from SimpleAES import SimpleAES


class MixListener(object):
    def __init__(self, privkey=None):
        if not privkey:
            print("No PrivateKey")
            sys.exit
        self.privkey = privkey
        self.to_send = []

    def on_error(self, headers, message):
        print('received an error %s' % message)

    def on_message(self, headers, message):
        message = json.loads(message)
        crypted_key = base64.b64decode(message['KEY'])
        aes_key = rsa.decrypt(crypted_key, self.privkey)
        aes = SimpleAES(aes_key)
        data = aes.decrypt(message['DATA'])

        if message['TO'] == '':
            print(message['FROM'] + ': ' + data)
        else:
            print('Message relayed')
            self.to_send.append(data)
            if len(self.to_send) > 3:
                random.shuffle(self.to_send)
                for data in self.to_send:
                    try:
                        conn = stomp.StompConnection10([(message['TO'], 61613)])
                        conn.start()
                        conn.connect()
                        conn.send(body=data, destination='/queue/to_send')
                        conn.disconnect
                    except:
                        print("REMOTE HOST NOT AVAILABLE")
                self.to_send = []


def main():
    # Do we have our OWN Keys?
    if not (os.path.isfile('./privkey.pem') and os.path.isfile('./pubkey.pem')):
        (pubkey, privkey) = rsa.newkeys(512)
        with open("privkey.pem", 'w') as keyfile:
            keyfile.write(privkey.save_pkcs1())
        with open("pubkey.pem", 'w') as keyfile:
            keyfile.write(pubkey.save_pkcs1())
    else:
        with open("privkey.pem") as keyfile:
            keydata = keyfile.read()
            privkey = rsa.PrivateKey.load_pkcs1(keydata)
        with open("pubkey.pem") as keyfile:
            keydata = keyfile.read()
            pubkey = rsa.PublicKey.load_pkcs1(keydata)

    # After this, we can use pubkey and privkey as our keypair for encryption

    # Connect to stomp and fetch messages
    conn = stomp.StompConnection10()
    conn.set_listener('', MixListener(privkey))
    conn.start()
    conn.connect()
    conn.subscribe(destination='/queue/to_send', id=1, ack='auto')

    # Yes we do this :-)
    while (True):
        time.sleep(10)


if __name__ == "__main__":
    main()
