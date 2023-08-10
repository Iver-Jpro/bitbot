from microbit import *

# Set up the serial connection
uart.init(baudrate=115200)

display.show(Image.BUTTERFLY)


while True:
    if uart.any():
        data_received = uart.read()
        display.scroll(data_received)
        uart.write("Ack!")
        display.show(Image.HEART)