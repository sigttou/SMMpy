#!/usr/bin/env python2
# -*- coding: utf-8 -*-
__author__ = "David Bidner, Rene Höbling and Alexander Wachter"
__license__ = "BSD 2-Clause"
__version__ = "1.0.0"
__status__ = "Released"

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
from settings import STOMP_PORT, MAX_QUEUE_SIZE, QUEUE, KEY_PATH


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

        # Tracker things:
        if(message.get('TYPE') == "INFO"):
            data = message['DATA']
            for entry in data:
                with open(KEY_PATH + entry, 'w') as storage:
                    storage.write(data[entry])
            return

        if(message.get('TYPE') == "REQ"):
            info = {}
            response = {}
            response['TYPE'] = "INFO"

            for entry in os.listdir(KEY_PATH):
                with open(KEY_PATH + entry, 'r') as content:
                    info[entry] = content.read()
            response['DATA'] = info

            response = json.dumps(response)

            address = message['FROM'].split(":")[0]
            port = STOMP_PORT
            if len(message['FROM'].split(":")) == 2:
                port = message['FROM'].split(":")[1]

            try:
                conn = stomp.StompConnection10([(address, port)])
                conn.start()
                conn.connect()
                conn.send(body=response, destination=QUEUE)
                conn.disconnect
            except:
                print("REMOTE HOST NOT AVAILABLE")
            return

        # Any other message
        crypted_key = base64.b64decode(message['KEY'])
        aes_key = rsa.decrypt(crypted_key, self.privkey)
        aes = SimpleAES(aes_key)
        data = aes.decrypt(base64.b64decode(message['DATA']))

        if message['TO'] == '':
            print(message['FROM'] + ': ' + data)
        else:
            print('Relaying message to: %s' % message['TO'])
            self.to_send.append(data)
            if len(self.to_send) > MAX_QUEUE_SIZE:
                random.shuffle(self.to_send)
                for data in self.to_send:
                    address = message['TO'].split(":")[0]
                    port = STOMP_PORT
                    if len(message['TO'].split(":")) == 2:
                        port = message['TO'].split(":")[1]

                    try:
                        conn = stomp.StompConnection10([(address, port)])
                        conn.start()
                        conn.connect()
                        conn.send(body=data, destination=QUEUE)
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
    conn.subscribe(destination=QUEUE, id=1, ack='auto')

    # Yes we do this :-)
    while (True):
        time.sleep(10)


if __name__ == "__main__":
    main()
