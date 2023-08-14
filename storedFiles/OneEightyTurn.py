import neopixel
from microbit import *

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
        if (redVal != None):
            value = redVal[0]

    except OSError:
        pass
    if (value & mask) > 0:
        return 1
    else:
        return 0


controlWait = 3
forwardTorque = 160
reverseTorque = 160
# adjustTorque = 200

mainTorque = 300
adjustTorque = 200

hasSeenLineR = False
hasTurned = False
waitToTurn = False
startedTurn = False

display.show(Image.HAPPY)

fireleds = neopixel.NeoPixel(pin13, 12)
for pixel_id in range(0, 11):
    fireleds[pixel_id] = (40, 0, 40)
    fireleds.show()
    sleep(30)
    fireleds[pixel_id] = (0, 0, 0)
    fireleds.show()

# waiting to start
for pixel_id in range(0, 11):
    fireleds[pixel_id] = (0, 0, 60)
fireleds.show()

sleep(3000)

runForSeconds = 5
startTime = running_time()

timeToWait = 100
waitStartTime = -1

# robots, start your engines!
pin16.write_analog(0)
pin8.write_analog(0)

pin14.write_analog(0)
pin12.write_analog(0)

linesPassed = 0
isOnLine = False


def initTurn180():
    global linesPassed
    global isOnLine
    if (linesensor(LEFT) == 1):
        linesPassed = 0
        isOnLine = True
    else:
        linesPassed = 1
        isOnLine = False


initTurn180()


def turn180():
    global linesPassed
    global isOnLine
    global hasTurned
    if (isOnLine == True):
        if (linesensor(LEFT) == 0):
            linesPassed += 1
            isOnLine = False
    elif (linesensor(LEFT) == 1):
        isOnLine = True

    if (linesPassed == 3):
        hasTurned = True
        pin16.write_analog(0)
        pin8.write_analog(0)

        pin14.write_analog(0)
        pin12.write_analog(0)
        return

    pin16.write_analog(0)
    pin8.write_analog(mainTorque)

    pin14.write_analog(mainTorque)
    pin12.write_analog(0)


# def turnRight():
#     global hasSeenLine
#     global hasTurned
#     if(linesensor(RIGHT) == 1):
#         hasSeenLine = True
#     if(hasSeenLine==True and linesensor(RIGHT) == 0):
#         pin16.write_analog(0)
#         pin14.write_analog(0)
#         pin8.write_analog(0)
#         pin12.write_analog(0)
#         hasTurned = True
#     else:
#         pin16.write_analog(forwardTorque)
#         pin14.write_analog(0)
#         pin12.write_analog(reverseTorque)
#         pin8.write_analog(0)

while True:
    if (running_time() - startTime > runForSeconds * 1000):
        break

    for pixel_id in range(0, 11):
        fireleds[pixel_id] = (0, 0, 0)
    if (linesensor(LEFT) == 1):
        for pixel_id in range(0, 5):
            fireleds[pixel_id] = (0, 50, 0)
    if (linesensor(RIGHT) == 1):
        for pixel_id in range(6, 11):
            fireleds[pixel_id] = (0, 50, 0)
    fireleds.show()

    turn180()
    if (hasTurned == True):
        break

    sleep(controlWait)

# turn off motors and lights
for pixel_id in range(0, 11):
    fireleds[pixel_id] = (40, 0, 40)
fireleds.show()

pin16.write_digital(0)
pin8.write_digital(0)

pin14.write_digital(0)
pin12.write_digital(0)
