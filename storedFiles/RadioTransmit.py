# RADIOTRANSMIT
from microbit import *
import radio

# Set up the serial connection
uart.init(baudrate=115200)

display.show(Image.HOUSE)

PACKET_SIZE = 64

def pad_string(input_str, size, pad_char='#'):
    padding = pad_char * (size - len(input_str))
    return input_str + padding

# configure the radio
MAX_MSG_LENGTH = 251
#radio.config(length=MAX_MSG_LENGTH, channel=22, power=7, address=0x276E5F98)
radio.config(length=MAX_MSG_LENGTH, channel=14, power=7, address=0x6795221E)

# turn on the radio
radio.on()

while True:
    if uart.any():
        sleep(100)
        data_received = uart.read()
        try:
            #dette fungerer dårlig for unicode tegn som havner i to bytes. Hvis vi absolutt ha norske bokstaver kan vi bruke ISO-8859-1
            utf8_string = data_received.decode('utf-8').rstrip()
        except UnicodeDecodeError:
            continue

        display.show(Image.ARROW_N)
        radio.send(utf8_string)

    message = radio.receive()
    if (message != None):
        display.show(Image.ARROW_S)

        sleep(2)
        uart.write(message+'\n')
        #uart.write(pad_string(message, PACKET_SIZE))
