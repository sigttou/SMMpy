# SMMpy
Stomp Mixed Messaging in python

## Setup
- Get an own env for your python project (run in the repo folder)
```
$ virtualenv-2.7 --distribute --no-site-packages env
$ source env/bin/activate
(env) $ pip install CoilMQ rsa SimpleAES stomp.py
```

## Documentation
### CoilMQ
Nothing was changed in the CoilMQ code just make sure you are running it.
Every other Stomp server supporting Version 1.0 should work too.

### Server
This is our core, it reads messages and relays them to other servers.

### Client
This script handles the packaging of the message.

### Keys
Currently all public keys should be placed in the `./keys` folder and be named like:
`address.pem`

### Tracker
This just fetches info and creates the key files

## Requirements
```
$ pip freeze
CoilMQ==0.6.1
SimpleAES==1.0
pyasn1==0.1.7
pycrypto==2.6.1
rsa==3.1.4
stomp.py==4.0.12
stompclient==0.3.2
```

## Usage
- Start `coilmq -b 0.0.0.0`
- run `python server.py`
- use `python client.py`

## TODO
* IMP: Usage (average)
* IMP: Tracker (average)
* IMP: Support STOMP 1.3 (low)
* IMP: Merge client, server, tracker
