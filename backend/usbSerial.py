import serial

ser = serial.Serial('COM3', 115200)  # Change 'COM3' to the appropriate COM port
ser.timeout = 10

ser.write(b'Hallo Marius!')
response = ser.read(100)
print('Received:', response)
ser.close()