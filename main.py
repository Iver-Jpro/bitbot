from microbit import *

# Set up the serial connection
uart.init(baudrate=115200)

display.show(Image.HAPPY)


while True:
    if uart.any():
        data_received = uart.read()
        display.scroll(data_received)
        uart.write(data_received)
        display.show(Image.HEART)


        # configure the radio
    radio.config(channel=7, power=7)

    # turn on the radio
    radio.on()
    while True:
        # receive a message
        message = radio.receive()
        if(message == "right"):


            radio.send("reverse")