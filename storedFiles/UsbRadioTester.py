import random
import time
from datetime import datetime

import serial
import uuid

sendt = []
recvt = []

ser = serial.Serial('COM4', 115200)  # Change 'COM3' to the appropriate COM port
ser.timeout = 1
nextTransmit = 0

terminator = '$$$'
partialMessage = ''
readyMessage = None

while True:
    #time.sleep(3)
    current_time = datetime.now()
    if (nextTransmit < time.time()):
        msg = str(uuid.uuid4())
        print(f'{current_time}:Sending:', msg)
        sendt.append(msg)

        ser.write((msg+terminator).encode('utf-8'))

        nextTransmit = time.time() + random.randint(10, 20)
    if(ser.in_waiting > 0):
        #time.sleep(0.1)#wait for buffer to fill up
        response = ser.read(39)  # waits for 1 second
        #print(response)

        #if response != b'':
        utf8_string= response.decode('utf-8').rstrip()
        print(f'{current_time}:USB:', utf8_string)
        if utf8_string.find(terminator) == -1:
            partialMessage = partialMessage + utf8_string
            print('partial message:', partialMessage)
        else:
            if utf8_string[-3:] != terminator and utf8_string.find("BROADCASTING") == -1:
                raise ValueError('terminator not at end of string')
            if utf8_string.count(terminator) > 1 and utf8_string.find("BROADCASTING") == -1:
                raise ValueError('more than one terminator in string')
            readyMessage = (partialMessage + utf8_string).strip(terminator)
            partialMessage = ''

        if readyMessage != None:
            print(f'{current_time}:Received:', readyMessage)
            if(readyMessage.find('!') == -1):
                thatSendt = sendt[len(recvt)]
                if (readyMessage != thatSendt):
                    print('ERROR: Expected', thatSendt)
                    print('ERROR: Received', readyMessage)
                    #break
                recvt.append(readyMessage)
                readyMessage = None


ser.close()
