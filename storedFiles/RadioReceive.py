# RADIO RECEIVE
from microbit import *
import radio
import random

terminator = '$$$'
MAX_MSG_LENGTH = 251

display.show(Image.HAPPY)

radiostrings = []
nextTransmit = 0

# configure the radio
radio.config(length=MAX_MSG_LENGTH, channel=7, power=7)
# turn on the radio
radio.on()

#partialMessage = ''
radioMessage = None

print("We are live!")

while True:
    #sleep(1000)
    data_received = radio.receive()
    if data_received != None:
        print("We got a message!")
        try:
            # dette fungerer dårlig for unicode tegn som havner i to bytes. Hvis vi absolutt ha norske bokstaver kan vi bruke ISO-8859-1
            utf8_string = data_received.decode('utf-8')
        except UnicodeDecodeError:
            print("The byte array was not valid UTF-8")
            continue
        radioMessage = utf8_string

        # if utf8_string.find(terminator) == -1:
        #     partialMessage = partialMessage + utf8_string
        #     print('partial message:', partialMessage)
        # else:
        #     if utf8_string[-3:] != terminator:
        #         raise ValueError('terminator not at end of string')
        #     if utf8_string.count(terminator) > 1:
        #         raise ValueError('more than one terminator in string')
        #     radioMessage = partialMessage + utf8_string
        #     partialMessage = ''

        #if radioMessage != None:
        print('Message ready to transmit:', radioMessage)
        # TODO: remove terminator
        radiostrings.append(radioMessage)
        display.show(radioMessage[0])

        radioMessage = None
        if nextTransmit == 0:
            nextTransmit = running_time() + (random.randint(0, 60) * 1000) + 10

    if nextTransmit != 0 and running_time() > nextTransmit:

        if len(radiostrings) > 0:
            pop = radiostrings.pop(0)
            print('Sending messg:', pop)
            # Todo: add terminator
            radio.send(pop)
        if len(radiostrings) == 0:
            nextTransmit = 0
        else:
            nextTransmit = running_time() + (random.randint(0, 60) * 1000) + 10
