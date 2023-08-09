from microbit import *
import radio
import neopixel

__I2CADDR = 0x1c  # address of PCA9557
RIGHT = "right"
LEFT = "left"



def linesensor(direction):
    """Read line sensor."""

    dir = direction
    if dir == LEFT:
        return getLine(0)
    elif dir == RIGHT:
        return getLine(1)

def getLine(bit):
    """Reads value of left or right line sensor."""

    mask = 1 << bit
    value = 0
    try:
        redVal = i2c.read(__I2CADDR, 1)
        if(redVal != None):
            value = redVal[0]

    except OSError:
        pass
    if (value & mask) > 0:
        return 1
    else:
        return 0


controlWait = 3
turnTorque = 300
adjustTorque = 200

display.show(Image.HAPPY)

fireleds = neopixel.NeoPixel(pin13, 12)
for pixel_id in range(0, 11):
    fireleds[pixel_id] = (40,0,40)
    fireleds.show()
    sleep(30)
    fireleds[pixel_id] = (0, 0, 0)
    fireleds.show()

#waiting to start
for pixel_id in range(0, 11):
    fireleds[pixel_id] = (0, 0, 60)
fireleds.show()

sleep(3000)

runForSeconds = 3
startTime = running_time()

#robots, start your engines!
pin16.write_analog(turnTorque)
pin8.write_analog(0)

pin14.write_analog(turnTorque)
pin12.write_analog(0)


def flashRed():
    for pixel_id in range(0, 11):
        fireleds[pixel_id] = (40,0,00)
        fireleds.show()
        sleep(30)
        fireleds[pixel_id] = (0, 0, 0)
        fireleds.show()


while True:
    if(running_time() - startTime > runForSeconds * 1000):
        break

    for pixel_id in range(0, 11):
        fireleds[pixel_id] = (0, 0, 0)
    if (linesensor(LEFT) == 1):
        for pixel_id in range(0, 5):
            fireleds[pixel_id] = (0,50,0)
    if (linesensor(RIGHT) == 1):
        for pixel_id in range(6, 11):
            fireleds[pixel_id] = (0,50,0)
    fireleds.show()

    #drive the robot
    if (linesensor(RIGHT) == 1):
        pin16.write_analog(turnTorque)
        pin14.write_analog(adjustTorque)

        # Adjusts direction. Arguments need to have very small values.
    elif (linesensor(LEFT) == 1):
        pin16.write_analog(adjustTorque)
        pin14.write_analog(turnTorque)


        # Adjusts direction. Arguments need to have very small values.
    else:
        pin16.write_analog(turnTorque)
        pin14.write_analog(turnTorque)

    sleep(controlWait)

#turn off motors and lights
for pixel_id in range(0, 11):
    fireleds[pixel_id] = (40, 0, 40)
fireleds.show()

pin16.write_digital(0)
pin8.write_digital(0)

pin14.write_digital(0)
pin12.write_digital(0)