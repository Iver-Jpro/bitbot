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
            if(redVal != None):
                value = redVal[0]

        except OSError:
            pass
        if (value & mask) > 0:
            return 1
        else:
            return 0
