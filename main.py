_C='is_ready exception'
_B=False
_A=True
from microbit import*
from micropython import const
import math,neopixel,radio
class RFIDState:READY=1;PINGED=2;PING_COMPLETED=3;ACKED=4;ACK_COMPLETED=5
_PREAMBLE=const(0)
_STARTCODE1=const(0)
_STARTCODE2=const(255)
_POSTAMBLE=const(0)
_HOSTTOPN532=const(212)
_PN532TOHOST=const(213)
_COMMAND_SAMCONFIGURATION=const(20)
_COMMAND_INLISTPASSIVETARGET=const(74)
_MIFARE_ISO14443A=const(0)
MIFARE_CMD_READ=const(48)
MIFARE_CMD_WRITE=const(160)
MIFARE_ULTRALIGHT_CMD_WRITE=const(162)
_ACK=b'\x00\x00\xff\x00\xff\x00'
_FRAME_START=b'\x00\x00\xff'
_I2C_ADDRESS=const(36)
_NOT_BUSY=const(1)
class BusyError(Exception):0
class PN532:
	def __init__(self,i2c,*,irq=None,req=None,debug=_B):self.debug=debug;self._irq=irq;self._req=req;self._i2c=i2c;self.state=RFIDState.READY;self.initialised=_B
	def _read_data(self,count):
		if self.debug:print('_read_data')
		status_byte=self._i2c.read(_I2C_ADDRESS,1)
		if self.debug:print('_read_data status_byte: ',status_byte)
		if status_byte[0]!=_NOT_BUSY:
			if self.debug:print('_read_data busy_error ')
			raise BusyError
		if self.debug:print('_read_data readfrom_into')
		frame=self._i2c.read(_I2C_ADDRESS,count)
		if self.debug:print('_read_data frame: ',frame)
		return frame
	def _write_data(self,framebytes):
		try:
			if self.debug:print('_write data: ',[hex(i)for i in framebytes])
			self._i2c.write(_I2C_ADDRESS,framebytes)
		except(OSError,RuntimeError):
			if self.debug:print(_C)
	def _write_frame(self,data):
		length=len(data);frame=bytearray(length+8);frame[0]=_PREAMBLE;frame[1]=_STARTCODE1;frame[2]=_STARTCODE2;checksum=sum(frame[0:3]);frame[3]=length&255;frame[4]=~length+1&255
		for x in range(length):frame[5+x]=data[x]
		checksum+=sum(data);frame[-2]=~checksum&255;frame[-1]=_POSTAMBLE
		if self.debug:print('Write frame: ',[hex(i)for i in frame])
		self._write_data(bytes(frame))
	def write_command(self,command,params=[]):
		data=bytearray(2+len(params));data[0]=_HOSTTOPN532;data[1]=command&255
		for(i,val)in enumerate(params):data[2+i]=val
		try:self._write_frame(data)
		except OSError:
			if self.debug:print('write_command OSError')
	def _read_frame(self,length):
		A='Response frame preamble does not contain 0x00FF!';response=self._read_data(length+8)
		if self.debug:print('Read frame:',[hex(i)for i in response])
		offset=0
		while response[offset]==0:
			offset+=1
			if offset>=len(response):raise RuntimeError(A)
		if response[offset]!=255:raise RuntimeError(A)
		offset+=1
		if offset>=len(response):raise RuntimeError('Response contains no data!')
		frame_len=response[offset]
		if frame_len+response[offset+1]&255!=0:raise RuntimeError('Response length checksum did not match length!')
		checksum=sum(response[offset+2:offset+2+frame_len+1])&255
		if checksum!=0:raise RuntimeError('Response checksum did not match expected value: ',checksum)
		return response[offset+2:offset+2+frame_len]
	def is_ready(self):
		status=bytearray(1)
		try:status=self._i2c.read(_I2C_ADDRESS,1)
		except OSError:
			if self.debug:print(_C)
		if status!=b'\x00':print('status:',status)
		return status==b'\x01'
	def got_ack(self):return self._read_data(len(_ACK))==_ACK
	def get_card_id(self,command,response_length=0):
		response=self._read_frame(response_length+2)
		if not(response[0]==_PN532TOHOST and response[1]==command+1):raise RuntimeError('Received unexpected command response!')
		return response[2:]
	def handle_rfid(self):
		if self.state==RFIDState.READY:
			if not self.initialised:self.write_command(_COMMAND_SAMCONFIGURATION,params=[1,2,1])
			else:print('ping card');self.write_command(_COMMAND_INLISTPASSIVETARGET,params=[1,_MIFARE_ISO14443A])
			self.state=RFIDState.PINGED
		elif self.state==RFIDState.PINGED:
			if self.is_ready():self.state=RFIDState.PING_COMPLETED
		elif self.state==RFIDState.PING_COMPLETED:print('ping completed')
		elif self.state==RFIDState.ACKED:
			print('acked')
			if self.is_ready():self.state=RFIDState.ACK_COMPLETED
		elif self.state==RFIDState.ACK_COMPLETED:
			if not self.initialised:print('init completed');self.initialised=_A;self.state=RFIDState.READY
			else:
				response=self.get_card_id(_COMMAND_INLISTPASSIVETARGET,response_length=19)
				if response is None:return
				if response[0]!=1:raise RuntimeError('More than one card detected!')
				if response[5]>7:raise RuntimeError('Found card with unexpectedly long UID!')
				print('card found');self.state=RFIDState.READY;return response[6:6+response[5]]
class Command:
	def __init__(self,opcode,duration,useLeftMotor,useRightMotor):self.opcode=opcode;self.duration=duration;self.useLeftMotor=useLeftMotor;self.useRightMotor=useRightMotor
speed=277./1e3
wheelbase=117.
breakTime=300
gameTime=20000
tagDisplayTime=2000
torque=4e2
leftAdjust=1.
rightAdjust=1.1
commands=[]
currentOpcode=''
currentOpcodeEnd=0
mostRecentTagTime=0
fireleds=neopixel.NeoPixel(pin13,12)
def degreesToLength(degrees):return wheelbase*2*math.pi*(degrees/36e1)
def lengthToTime(length):return length/speed
def drive(useLeftMotor,useRightMotor):
	if _B:pin16.write_analog(torque*leftAdjust);pin8.write_digital(0)
	if _B:pin14.write_analog(torque*rightAdjust);pin12.write_digital(0)
def setLEDs(brightness):
	for pixel_id in range(0,11):fireleds[pixel_id]=0,int(255.*brightness),0
	fireleds.show()
def stop():pin16.write_digital(0);pin8.write_digital(0);pin14.write_digital(0);pin12.write_digital(0)
def appendForward(length):commands.append(Command('forward',lengthToTime(length),_A,_A))
def appendLeft(degrees):commands.append(Command('left',lengthToTime(degreesToLength(degrees)),_B,_A))
def appendRight(degrees):commands.append(Command('right',lengthToTime(degreesToLength(degrees)),_A,_B))
def initializeNextRun():setLEDs(.0);global currentOpcode;global currentOpcodeEnd;currentOpcode='';currentOpcodeEnd=0;global mostRecentTagTime;mostRecentTagTime=0;commands.clear();display.on();display.scroll('READY');appendForward(2e2);appendLeft(9e1);appendForward(1e2);appendRight(18e1);appendForward(1e2);appendLeft(9e1);appendForward(2e2)
def endRun():stop();display.off()
radio.config(channel=7,power=7)
radio.on()
pn532=PN532(i2c,debug=_A)
while _A:
	initializeNextRun();currentGameStartTime=running_time();previouslyDisplayedRemainingTime=6
	while _A:
		runningTime=running_time()
		if runningTime>=currentGameStartTime+gameTime:break
		remainingTime=int((currentGameStartTime+gameTime-runningTime)/1e3)
		if remainingTime<previouslyDisplayedRemainingTime:previouslyDisplayedRemainingTime=remainingTime;display.scroll(remainingTime,wait=_B)
		if not commands and runningTime>=currentOpcodeEnd:break
		if runningTime>=currentOpcodeEnd:
			if currentOpcode=='':command=commands[0];currentOpcode=command.opcode;currentOpcodeEnd=runningTime+command.duration;drive(command.useLeftMotor,command.useRightMotor);commands.pop(0)
			else:currentOpcodeEnd=currentOpcodeEnd+breakTime;stop();currentOpcode=''
		pn532.handle_rfid()
		if runningTime<=mostRecentTagTime+tagDisplayTime:setLEDs((mostRecentTagTime+tagDisplayTime-runningTime)/tagDisplayTime)
	endRun();break