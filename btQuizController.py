# Quiz Controller
# Python 3 version
#
# Author: Chris Noble
#
# Handles multiple Bluetooth clients (usually Android apps)
# Allows and controls question answering on a first-come-first-served basis
#
# Received from client:
# "9" - Answer button pressed
# "0" - special function (lock-out)
# "1" - special function (re-enable)
# "ka" - keep-alive
# "Name:*" - name of quizzer using client
#
# Send to client:
# "8" - lock-out
# "7" - unlock
#
# Flags and lists:
# clientStatus - dictionary of connected clients and status (sock:status)
# Status:
# 0 - not connected
# 1 - connected
# 2 - name entered (in game)
# 3 - answered
# 4 - locked-out due to answerer
# 5 - locked-out after incorrect answer
#
# Date: 19-Apr-2020
# Version history
# 27-Apr-2020 First working version

import bluetooth
import sys
import logging
import errno
import signal
from datetime import datetime
import time
#import selectors2 as selectors
import selectors

callReset = False
callLockoutAnswerer = False
currentAnswerer = bluetooth.BluetoothSocket()
host = "" # accept connections from any address

###################
# Control-C handler (or kill -SIGINT)
# Terminate program
def controlC_handler(sig, frame):
    logging.info('SIGINT received, terminating...')
    sys.exit(0)

signal.signal(signal.SIGINT, controlC_handler)

###################
# Sigusr1 handler (or kill -SIGUSR1)
# Send lock-out to all but current answerer
# NOT USED
def usr1_handler(sig, frame):
    logging.info('SIGUSR1 received...')

signal.signal(signal.SIGUSR1, usr1_handler)

###################
# Sigusr2 handler (or kill -SIGUSR2)
# Send lock to current answerer and unlock to others
def usr2_handler(sig, frame):
    global callLockoutAnswerer

    logging.info('SIGUSR2 received...')
    callLockoutAnswerer = True
    
signal.signal(signal.SIGUSR2, usr2_handler)

###################
# Sighup handler (or kill -SIGHUP)
# Send unlock to all (reset for next round)
def hup_handler(sig, frame):
    global callReset

    logging.info('SIGHUP received...')
    callReset = True

signal.signal(signal.SIGHUP, hup_handler)

####################
# Accept bluetooth connections
#
def accept(sock, mask):
        sock, addr = sock.accept()
        logging.info("Accepted %s from %s", sock, addr)
        clientStatus.update({sock:1})
        sock.setblocking(False)
        sel.register(sock, selectors.EVENT_READ, read_data)

def read_data(sock, mask):
        global currentAnswerer

        if mask & selectors.EVENT_READ:
                try:
                        # This times-out (usually, but not always) after first receive
                        # selector appears to incorrectly detect ready-to-receive
                        data = sock.recv(1024)
                        if data:
                                # 'ka' = keep-alive
                                # '9' = Answer button pressed
                                # '0' or '1' = test function
                                # anything else is labelled data, eg 'Name:Chris'
                                strData = data.decode("utf-8")
                                if strData == "0":
                                        print("Locked-out")
                                        sock.send(b"8")
                                elif strData == "1":
                                        callLockoutAnswerer = True
                                        print("Unlocked")
                                        sock.send(b"7")
                                elif strData == "9":
                                        if currentAnswerer == serverSock:
                                                currentAnswerer = sock
                                                print("\nAnswered by ", clientName.get(sock, "Name not found"), " at ", sock)
                                                sock.send(b"9")
                                                clientStatus.update({sock:3})
                                                # lock-out all other clients
                                                for x, y in clientStatus.items():
                                                        if sock != x and y == 2:
                                                                x.send(b"8")
                                                                clientStatus.update({x:4})
                                        else:
                                                print("\nJust too late: ", clientName.get(sock, "Name not found"), " at ", sock)
                                elif strData == "ka":
                                        sys.stdout.write('.')
                                        sys.stdout.flush()
                                elif strData.startswith("Name:"):
                                        clientStatus.update({sock:2})
                                        theName = strData.partition(":")[2]
                                        clientName.update({sock:theName})
                                else:
                                        logging.info(strData)
                        else:
                                logging.info("Connection close received - closing connection")
                                sel.unregister(sock)
                                sock.close()
                                clientStatus.pop(sock)
                                currentAnswerer = serverSock
                except bluetooth.BluetoothError as e:
                        logging.info("BluetoothError")
                        logging.info("disconnected")
                        sel.unregister(sock)
                        sock.close
                        clientStatus.pop(sock)
                        currentAnswerer = serverSock
                except:
                        logging.info("System error: %s", sys.exc_info()[0] )
                        exit(1)

                
logging.basicConfig(filename='btQuizController.log',level=logging.INFO)
#logging.basicConfig(level=logging.INFO)

# Creating Socket Bluetooth RFCOMM communication
sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
serverSock = sock
currentAnswerer = serverSock

logging.info('Bluetooth Socket Created')

sock.bind((host, bluetooth.PORT_ANY))
logging.info("Bluetooth Binding Completed")

sock.listen(1) 
sock.setblocking(False)

sel = selectors.DefaultSelector()
events = selectors.EVENT_READ
sel.register(sock, events, accept)

# sock:status
clientStatus = {
}


# sock:name
clientName = {
}

while True:
        # Wait for some data from the far end
        myEvents = sel.select(timeout=0.5)
        if not myEvents:
                # Perform some housekeeping
                if callLockoutAnswerer == True:  # and currentAnswerer != serverSock:
                        logging.info("Lockout current answerer called")
                        if currentAnswerer != serverSock:
                                currentAnswerer.send(b"8")
                                clientStatus.update({currentAnswerer:5})
                        else:
                                logging.info("currentAnswerer == serverSock (%s : %s)", currentAnswerer, serverSock)

                        # unlock all other relevant clients
                        for x, y in clientStatus.items():
                                if sock != x and y == 4:
                                        x.send(b"7")
                                        clientStatus.update({x:2})

                        currentAnswerer = serverSock
                        callLockoutAnswerer = False
                elif callReset == True:
                        logging.info("Reset game called")
                        # unlock all clients
                        for x, y in clientStatus.items():
                                if y > 2:
                                        x.send(b"7")
                                        clientStatus.update({x:2})

                        currentAnswerer = serverSock
                        callReset = False
        else:
                try:
                        for key, mask in myEvents:
                                callback = key.data
                                try:
                                        callback(key.fileobj, mask)
                                except IndexError as e:
                                        #logging.info("Client disconnected, error: %s", e)
                                        exit(1)
                                except:
                                        #logging.info("myEvents Exception: %s", e)
                                        exit(1)

                except Exception as e:
                        logging.info("select failed to return anything useful")

