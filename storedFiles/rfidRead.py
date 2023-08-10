from microbit import *
from micropython import const

class RFIDState:
    READY = 1
    PINGED = 2
    PING_COMPLETED = 3
    ACKED = 4
    ACK_COMPLETED = 5

_PREAMBLE = const(0x00)
_STARTCODE1 = const(0x00)
_STARTCODE2 = const(0xFF)
_POSTAMBLE = const(0x00)

_HOSTTOPN532 = const(0xD4)
_PN532TOHOST = const(0xD5)

# PN532 Commands
_COMMAND_SAMCONFIGURATION = const(0x14)
_COMMAND_INLISTPASSIVETARGET = const(0x4A)

_MIFARE_ISO14443A = const(0x00)

# Mifare Commands
MIFARE_CMD_READ = const(0x30)
MIFARE_CMD_WRITE = const(0xA0)
MIFARE_ULTRALIGHT_CMD_WRITE = const(0xA2)

_ACK = b'\x00\x00\xFF\x00\xFF\x00'
_FRAME_START = b'\x00\x00\xFF'

_I2C_ADDRESS = const(0x24)
_NOT_BUSY = const(0x01)


class BusyError(Exception):
    pass

class PN532:
    def __init__(self, i2c, *, irq=None, req=None, debug=False):
        self.debug = debug
        self._irq = irq
        self._req = req
        self._i2c = i2c
        self.state = RFIDState.READY
        self.initialised = False
        return

    def _read_data(self, count):
        print("_rd")
        frame = self._i2c.read(_I2C_ADDRESS, count+1)
        print("_rd frame: ", frame)
        if frame[0] != _NOT_BUSY:
            return None
        return frame[1:]

    def _write_data(self, framebytes):
        try:
            print('_wd: ', [hex(i) for i in framebytes])
            self._i2c.write(_I2C_ADDRESS, framebytes)
        except (OSError, RuntimeError):
            print("_wd: exception")
        print('_wd: data written')

    def _write_frame(self, data):
        assert data is not None and 1 < len(
            data) < 255, 'Data must be 1-255 bytes.'
        # Build frame to send as:
        # - Preamble (0x00)
        # - Start code  (0x00, 0xFF)
        # - Command length (1 byte)
        # - Command length checksum
        # - Command bytes
        # - Checksum
        # - Postamble (0x00)
        length = len(data)
        frame = bytearray(length+7)
        frame[0] = _PREAMBLE
        frame[1] = _STARTCODE1
        frame[2] = _STARTCODE2
        checksum = sum(frame[0:3])
        frame[3] = length & 0xFF
        frame[4] = (~length + 1) & 0xFF
        for x in range(length):
            frame[5+x] = data[x]
        checksum += sum(data)
        frame[-2] = (~checksum & 0xFF)
        frame[-1] = _POSTAMBLE
        self._write_data(bytes(frame))

    def write_command(self, command, params=[]):
        data = bytearray(2+len(params))
        data[0] = _HOSTTOPN532
        data[1] = command & 0xFF
        for i, val in enumerate(params):
            data[2+i] = val

        try:
            self._write_frame(data)
        except OSError:
            if self.debug:
                print("write_command OSError")

    def _read_frame(self, length):
        response = self._read_data(length+8)
        if self.debug:
            print('Read frame:', [hex(i) for i in response])

        # Swallow all the 0x00 values that preceed 0xFF.
        offset = 0
        while response[offset] == 0x00:
            offset += 1
            if offset >= len(response):
                raise RuntimeError(
                    'Response frame preamble does not contain 0xFF!')
        if response[offset] != 0xFF:
            raise RuntimeError(
                'Response frame preamble does not contain 0xFF!')
        offset += 1
        if offset >= len(response):
            raise RuntimeError('Response contains no data!')
        # Check length & length checksum match.
        frame_len = response[offset]
        if (frame_len + response[offset+1]) & 0xFF != 0:
            raise RuntimeError(
                'Response length checksum mismatch')
        # Check frame checksum value matches bytes.
        checksum = sum(response[offset+2:offset+2+frame_len+1]) & 0xFF
        if checksum != 0:
            raise RuntimeError(
                'Response checksum mismatch:', checksum)
        # Return frame data.
        return response[offset+2:offset+2+frame_len]

    def is_ready(self):
        status = bytearray(1)
        try:
            status = self._i2c.read(_I2C_ADDRESS, 1)
        except OSError:
            if self.debug:
                print("is_ready exception")
        if status != b'\x00':
            print("status:", status)
        return status == b'\x01'

    def got_ack(self):
        print("Check for ACK")
        return self._read_data(len(_ACK)) == _ACK

    def get_card_id(self, command, response_length=0):
        response = self._read_frame(response_length+2)
        if not (response[0] == _PN532TOHOST and response[1] == (command+1)):
            raise RuntimeError('Received unexpected command response!')
        return response[2:]

    def handle_rfid(self):
        # return a bytearray with the UID if a card is detected.
        if self.state == RFIDState.READY:
            if not self.initialised:
                # - 0x01, normal mode
                # - 0x02, timeout 50ms * 2 = 100ms
                # - 0x01, use IRQ pin
                self.write_command(_COMMAND_SAMCONFIGURATION,
                                   params=[0x01, 0x02, 0x01])
            else:
                print("ping card")
                self.write_command(_COMMAND_INLISTPASSIVETARGET,
                                   params=[0x01, _MIFARE_ISO14443A])
            self.state = RFIDState.PINGED
        elif self.state == RFIDState.PINGED:
            if self.is_ready():
                self.state = RFIDState.PING_COMPLETED
        elif self.state == RFIDState.PING_COMPLETED:
            print("ping completed")
            if self.got_ack() is True:
                self.state = RFIDState.ACKED
        elif self.state == RFIDState.ACKED:
            print("acked")
            if self.is_ready():
                self.state = RFIDState.ACK_COMPLETED
        elif self.state == RFIDState.ACK_COMPLETED:
            if not self.initialised:
                print("init completed")
                self.initialised = True
                self.state = RFIDState.READY
            else:
                response = self.get_card_id(_COMMAND_INLISTPASSIVETARGET,
                                            response_length=19)
                if response is None:
                    return None

                # Check only 1 card with up to a 7 byte UID is present.
                if response[0] != 0x01:
                    raise RuntimeError('>1 card detected!')
                if response[5] > 7:
                    raise RuntimeError('Found card with long UID!')

                print("card found")
                self.state = RFIDState.READY
                # Return UID of card.
                return response[6:6+response[5]]


print("init I2C")
i2c.init()
if _I2C_ADDRESS in i2c.scan():
    print("Found PN532")
else:
    print("PN532 NOT found!!!")

pn532 = PN532(i2c, debug=True)

print("initialise")
pn532.write_command(_COMMAND_SAMCONFIGURATION, params=[0x01, 0x01, 0x00])

while not pn532.is_ready():
    sleep(1)

if not pn532.got_ack():
    print("Did not get ACK")

print("Search for one card")
pn532.write_command(_COMMAND_INLISTPASSIVETARGET, params=[0x01, _MIFARE_ISO14443A])

while not pn532.is_ready():
    sleep(1)

if not pn532.got_ack():
    print("Did not get ACK from readcard command")

print("ready to look for card?")

while not pn532.is_ready():
    sleep(1)

print("Did we find a card?")

response = pn532.get_card_id(_COMMAND_INLISTPASSIVETARGET, response_length=19)
if response is None:
    print("No card  :-(")
else:
    # Check only 1 card with up to a 7 byte UID is present.
    if response[0] != 0x01:
        print('>1 card detected!')
    elif response[5] > 7:
        print('Found card with long UID!')
    else:
        print("Found ", response[6:6+response[5]])
