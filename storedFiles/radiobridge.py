from microbit import *
import radio
import random

# Set up the serial connection
uart.init(baudrate=115200)

display.show(Image.HEART)

radiostrings = []
nextTransmit = 0

# configure the radio
radio.config(channel=7, power=7)
# turn on the radio
radio.on()

while True:
    if uart.any():
        data_received = uart.read()
        display.show(Image.ARROW_N)

        radio.send(data_received)
        #uart.write(data_received)


    message = radio.receive()
    if (message != None):
        display.show(Image.ARROW_S)
        uart.write(message)
