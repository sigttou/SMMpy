#!/usr/bin/env python2
# -*- coding: utf-8 -*-
__author__ = "David Bidner, Rene Höbling and Alexander Wachter"
__license__ = "BSD 2-Clause"
__version__ = "rolling"
__status__ = "Demo"

# Provides a simple CLI interface to send a message to another server

import stomp
import rsa
import os
import sys
import json
import base64
import binascii
from SimpleAES import SimpleAES

KEY_PATH = "./keys/"
LOCAL_NAME = "SET_YOUR_NAME"

# Fix Python 2.x.
try:
    input = raw_input
except NameError:
    pass


def get_message():
    """
    Asks the user about the message
    """
    message = input("What's on your mind?\n")
    return message


def get_servers(pubservers):
    """
    Scan the key folder for possible servers
    """
    for entry in os.listdir(KEY_PATH):
        address = os.path.splitext(entry)[0]
        with open(KEY_PATH + entry) as pubfile:
            keydata = pubfile.read()
        pubkey = rsa.PublicKey.load_pkcs1(keydata)
        pubservers[address] = pubkey

    return pubservers


def create_chain(pubservers):
    """
    Interacts with the user about which servers should be used
    """
    i = 0
    chain = []

    print("Available servers:")
    for server in pubservers.keys():
        print(str(i) + ': ' + server)
        i += 1

    try:
        receiver = int(input("Where do you want to send it? "))
    except:
        print("Give a valid receiver!")
        sys.exit()

    print("Chain starts sending with first server")
    nodes = input("Give server chain splitted with ,: ").split(',')
    nodes = filter(None, nodes)

    if len(nodes) > 0:
        nodes = map(int, nodes)
    else:
        print("WARN: direct sending!")
        nodes = []
    nodes.append(receiver)

    for node in nodes:
        print("Adding: " + pubservers.keys()[node])
        chain.append(
            (pubservers.keys()[node],
             pubservers[pubservers.keys()[node]]))
    return chain


def generate_message(chain, data):
    """
    Does a little bit of AES, RSA and json magic
    """
    with open("pubkey.pem") as keyfile:
        keydata = keyfile.read()

    local_pubkey = rsa.PublicKey.load_pkcs1(keydata)
    local_entry = ('', local_pubkey)
    chain = [local_entry] + chain

    # We start crypto from behind ;)
    content = {}
    i = 0
    to_address = ''
    for node in reversed(chain):
        (address, pubkey) = node
        content['TO'] = to_address
        if i > 0:
            content['FROM'] = ''
        else:
            content['FROM'] = LOCAL_NAME
        to_address = address

        aes_key = binascii.b2a_hex(os.urandom(15))
        aes = SimpleAES(aes_key)
        chipher_data = aes.encrypt(data)
        crypted_key = base64.b64encode(rsa.encrypt(aes_key, pubkey))
        content['DATA'] = chipher_data
        content['KEY'] = crypted_key
        data = json.dumps(content)
        i += 1

    return data


def send_message(message):
    """
    Sends the message to the localhost
    """
    try:
        conn = stomp.StompConnection10()
        conn.start()
        conn.connect()
        conn.send(body=message, destination='/queue/to_send')
        conn.disconnect
    except:
        print("There are Server Problems")


def main():
    pubservers = {}

    text = get_message()
    pubservers = get_servers(pubservers)
    chain = create_chain(pubservers)

    message = generate_message(chain, text)
    send_message(message)


if __name__ == "__main__":
    main()