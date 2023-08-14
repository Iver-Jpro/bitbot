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