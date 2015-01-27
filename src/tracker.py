#!/usr/bin/env python2
# -*- coding: utf-8 -*-
__author__ = "David Bidner, Rene Höbling and Alexander Wachter"
__license__ = "BSD 2-Clause"
__version__ = "rolling"
__status__ = "Demo"

# Provides a more or less complex structure for the SMM Network tracker
# For legacy usage we will keep the code splitted. (1.0 release will be merged)

"""
On the Tracker we will use following messages:
    TYPE: REQ,INFO
    FROM: "Address"
The used queue is queue/tracker
"""

import os.path
import time
import stomp
import json


KEY_PATH = "./keys/"


class MixListener(object):
    def on_error(self, headers, message):
        print('received an error %s' % message)

    def on_message(self, headers, message):
        message = json.loads(message)

        if(message.get('TYPE') == "INFO"):
            data = message['DATA']
            for entry in data:
                with open(KEY_PATH + entry, 'w') as storage:
                    storage.write(data[entry])

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
            port = 61613
            if len(message['FROM'].split(":")) == 2:
                port = message['FROM'].split(":")[1]

            try:
                conn = stomp.StompConnection10([(address, port)])
                conn.start()
                conn.connect()
                conn.send(body=response, destination='/queue/tracker')
                conn.disconnect
            except:
                print("REMOTE HOST NOT AVAILABLE")


def main():
    # Connect to stomp and fetch messages
    conn = stomp.StompConnection10()
    conn.set_listener('', MixListener())
    conn.start()
    conn.connect()
    conn.subscribe(destination='/queue/tracker', id=1, ack='auto')

    # Yes we do this :-)
    while (True):
        time.sleep(10)


if __name__ == "__main__":
    main()
