import serial

ser = serial.Serial('COM3', 115200)  # Change 'COM3' to the appropriate COM port
ser.timeout = 10

counter = 0

while counter < 100:
    teststring = counter.to_bytes(1, 'big')
    print('Sending:', teststring)
    ser.write(teststring)
    response = ser.read(100)
    print('Received:', response)
    counter += 1

ser.close()