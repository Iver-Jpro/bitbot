from microbit import *
import radio
import random

display.show(Image.HAPPY)

radiostrings = []
nextTransmit = 0

# configure the radio
radio.config(channel=7, power=7)
# turn on the radio
radio.on()

while True:
    message = radio.receive()

    if (message != None):
        resMes=radio.receive()
        while(resMes!=None):
            message.append(resMes)
            resMes=radio.receive()

        radiostrings.append(message)
        display.show(message[0])
        if (nextTransmit == 0):
            nextTransmit = running_time() + (random.randint(0, 60) * 1000) + 10

    if (nextTransmit != 0 and running_time() > nextTransmit):

        if (len(radiostrings) > 0):
            radio.send(radiostrings.pop(0))
        if (len(radiostrings) == 0):
            nextTransmit = 0
        else:
            nextTransmit = running_time() + (random.randint(0, 60) * 1000) + 10
