# RADIOTRANSMIT
from microbit import *
import radio

# Set up the serial connection
uart.init(baudrate=115200)

display.show(Image.HOUSE)

radiostrings = []
terminator = '$$$'

nextTransmit = 0

# configure the radio
MAX_MSG_LENGTH = 251
radio.config(length=MAX_MSG_LENGTH, channel=7, power=7)
# turn on the radio
radio.on()

partialMessage = ''
readyMessage = None

while True:
    if uart.any():
        data_received = uart.read()
        try:
            #dette fungerer dårlig for unicode tegn som havner i to bytes. Hvis vi absolutt ha norske bokstaver kan vi bruke ISO-8859-1
            utf8_string = data_received.decode('utf-8').rstrip()
        except UnicodeDecodeError:
            #print("!The byte array was not valid UTF-8")
            continue
        if utf8_string.find(terminator) == -1:
            partialMessage = partialMessage + utf8_string
            #print('!partial message:', partialMessage)
        else:
            if utf8_string[-3:] != terminator:
                raise ValueError('terminator not at end of string')
            if utf8_string.count(terminator) > 1:
                raise ValueError('more than one terminator in string')
            readyMessage = (partialMessage + utf8_string).strip(terminator)
            partialMessage = ''

        if readyMessage != None:
            if(len(readyMessage)>MAX_MSG_LENGTH):
                raise ValueError('message too long')

            display.show(Image.ARROW_N)

            #print('!USB message:', readyMessage)
            print("!!!!BROADCASTING +", readyMessage + terminator)
            radio.send(readyMessage)
            partialMessage = ''
            readyMessage=None

    message = radio.receive()
    if (message != None):
        display.show(Image.ARROW_S)
        #print("!!!!BROADCASTING +", message)
        sleep(2)
        uart.write(message+terminator)
