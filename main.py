_C=None
_B=True
_A=False
from micropython import const
import neopixel,radio
from microbit import*
class Globals:
    def __init__(self):self.MAX_MSG_LENGTH=251;self.cards={1057905702:Card(1,_B),1893419794:Card(1,_B),329147126:Card(1,_A),866861814:Card(1,_A),1664779766:Card(1,_A),1676494582:Card(1,_A),1944446709:Card(1,_A),2205734389:Card(1,_A),2214546422:Card(1,_A),3543034358:Card(1,_A),3554901238:Card(1,_A),4081897461:Card(1,_A)};self.gameTime=20000;self.tagDisplayTime=2000;self.tags=set();self.mostRecentTag=0;self.isOnTag=_A;self.mostRecentTagTime=0;self.fireleds=neopixel.NeoPixel(pin13,12);self.commands='';self.points=0;self.runIsStarted=_A
class Card:
    def __init__(self,points,isStartPoint):self.points=points;self.isStartPoint=isStartPoint
class RFIDCom:READY=1;WAITING_FOR_ACK=2;WAITING_FOR_RESPONSE=3
class BusyError(Exception):0
class PN532:
    PN532_ADDRESS=36;PREAMBLE=0;STARTCODE1=0;STARTCODE2=255;POSTAMBLE=0;HOSTTOPN532=212;PN532TOHOST=213;COMMAND_SAMCONFIGURATION=20;COMMAND_RFCONFIGURATION=50;COMMAND_INLISTPASSIVETARGET=74;ISO14443A=0;ACK=b'\x00\x00\xff\x00\xff\x00';FRAME_START=b'\x00\x00\xff';I2C_DELAY=10;I2C_CARD_POLL_TIMEOUT=10000
    def __init__(self,i2c):self._i2c=i2c;self.state=RFIDCom.READY;self.previousCommand=_C;self.previousCommandTime=0
    def writeData(self,frame):self._i2c.write(self.PN532_ADDRESS,frame)
    def writeFrame(self,data):
        length=len(data);frame=bytearray(length+7);frame[0]=self.PREAMBLE;frame[1]=self.STARTCODE1;frame[2]=self.STARTCODE2;checksum=sum(frame[0:3]);frame[3]=length&255;frame[4]=~length+1&255
        for x in range(length):frame[5+x]=data[x]
        checksum+=sum(data);frame[-2]=~checksum&255;frame[-1]=self.POSTAMBLE;self.writeData(bytes(frame))
    def writeCommand(self,command,params=[]):
        data=bytearray(2+len(params));data[0]=self.HOSTTOPN532;data[1]=command&255
        for(i,val)in enumerate(params):data[2+i]=val
        self.writeFrame(data);return command
    def readData(self,count):
        frame=self._i2c.read(self.PN532_ADDRESS,count+1)
        if frame[0]!=1:raise BusyError
        return frame[1:]
    def readFrame(self,length):
        response=self.readData(length+8)
        if response[0:3]!=self.FRAME_START:raise RuntimeError('Invalid response frame start')
        frameLen=response[3]
        if frameLen+response[4]&255!=0:raise RuntimeError('Response length checksum mismatch')
        checksum=sum(response[5:5+frameLen+1])&255
        if checksum!=0:raise RuntimeError('Response checksum mismatch:',checksum)
        return response[5:5+frameLen]
    def isReady(self):return self._i2c.read(self.PN532_ADDRESS,1)==b'\x01'
    def gotAck(self):return self.readData(len(self.ACK))==self.ACK
    def getCardId(self,command,responseLen):
        response=self.readFrame(responseLen+2)
        if not(response[0]==self.PN532TOHOST and response[1]==command+1):raise RuntimeError('Invalid card response')
        if response[2]!=1 or response[7]>7:raise RuntimeError('Unsupported card response')
        cardId=0
        for i in range(response[7]):cardId=cardId*256+response[8+i]
        return cardId
    def handleRFID(self,globals):
        try:
            currentRFIDTime=running_time()
            if currentRFIDTime<self.previousCommandTime+self.I2C_DELAY:return
            if self.previousCommand==self.COMMAND_INLISTPASSIVETARGET and currentRFIDTime>self.previousCommandTime+self.I2C_CARD_POLL_TIMEOUT:self.state=RFIDCom.READY
            if self.state!=RFIDCom.READY and not self.isReady():
                if currentRFIDTime>self.previousCommandTime+1000:self.state=RFIDCom.READY
                return
            self.previousCommandTime=currentRFIDTime
            if self.state==RFIDCom.READY:
                if self.previousCommand is _C:self.previousCommand=self.writeCommand(self.COMMAND_SAMCONFIGURATION,params=[1,0,1])
                elif self.previousCommand is self.COMMAND_SAMCONFIGURATION:self.previousCommand=self.writeCommand(self.COMMAND_RFCONFIGURATION,params=[1,1])
                else:self.previousCommand=self.writeCommand(self.COMMAND_INLISTPASSIVETARGET,params=[1,self.ISO14443A])
                self.state=RFIDCom.WAITING_FOR_ACK
            elif self.state==RFIDCom.WAITING_FOR_ACK:
                if self.gotAck():self.state=RFIDCom.WAITING_FOR_RESPONSE
            elif self.state==RFIDCom.WAITING_FOR_RESPONSE:
                if self.previousCommand is self.COMMAND_SAMCONFIGURATION:self.readFrame(0)
                elif self.previousCommand is self.COMMAND_RFCONFIGURATION:self.readFrame(0)
                elif self.previousCommand is self.COMMAND_INLISTPASSIVETARGET:
                    response=self.getCardId(self.COMMAND_INLISTPASSIVETARGET,responseLen=19)
                    if response is _C:globals.isOnTag=_A
                    else:
                        globals.isOnTag=_B
                        if response!=globals.mostRecentTag:drive.stop()
                        globals.mostRecentTag=response
                        if response not in globals.tags:
                            globals.tags.add(response)
                            if globals.runIsStarted:
                                globals.mostRecentTagTime=currentRFIDTime;print('new card found: ',response)
                                if response in globals.cards:globals.points=globals.points+globals.cards.get(response).points
                                else:globals.points=response
                                display.scroll(str(globals.points),wait=_A,loop=_B)
                        self.state=RFIDCom.READY;return response
                self.state=RFIDCom.READY
        except(OSError,RuntimeError,BusyError):pass
class DriveState:READY=1;TURNING_LEFT=2;TURNING_RIGHT=3;TURNING_AROUND=4;FORWARD=5
class Drive:
    LF_ADDRESS=const(28);LEFT_LF=const(1);RIGHT_LF=const(2);TORQUE=400;TURN_TORQUE=250;SLOW_TORQUE=0;EXPECTED_TURN_TIME=440;EXPECTED_U_TURN_TIME=1000;linesPassed=0;startedTurning=0;isOnLine=_A
    def __init__(self):self.state=DriveState.READY;self.stop()
    def getLinesensorStatus(self):
        try:
            value=i2c.read(self.LF_ADDRESS,1)
            if value is not _C:return value[0]&(self.LEFT_LF|self.RIGHT_LF)
        except OSError:pass
        return 0
    def adjustMotors(self,left,right):
        if left>=0:pin16.write_analog(left);pin8.write_analog(0)
        else:pin16.write_analog(0);pin8.write_analog(-left)
        if right>=0:pin14.write_analog(right);pin12.write_analog(0)
        else:pin14.write_analog(0);pin12.write_analog(-right)
    def stop(self):self.adjustMotors(0,0);self.state=DriveState.READY
    def turnLeft(self):
        if self.state==DriveState.READY:
            if self.getLinesensorStatus()&self.LEFT_LF:self.linesPassed=0;self.isOnLine=_B
            else:self.linesPassed=1;self.isOnLine=_A
            self.state=DriveState.TURNING_LEFT;self.adjustMotors(0,self.TURN_TORQUE);self.startedTurning=running_time()
        elif self.state==DriveState.TURNING_LEFT:self.keepTurning(self.LEFT_LF)
    def keepTurning(self,direction):
        status=self.getLinesensorStatus()
        if status&direction and running_time()-self.startedTurning>self.EXPECTED_TURN_TIME:
            self.adjustMotors(self.TORQUE,self.TORQUE);self.state=DriveState.FORWARD
            if direction==self.LEFT_LF:dircode='L'
            else:dircode='R'
            radio.send(dircode+': '+str(running_time()-self.startedTurning))
    def turnRight(self):
        if self.state==DriveState.READY:
            if self.getLinesensorStatus()&self.RIGHT_LF:self.linesPassed=0;self.isOnLine=_B
            else:self.linesPassed=1;self.isOnLine=_A
            self.state=DriveState.TURNING_RIGHT;self.adjustMotors(self.TURN_TORQUE,0);self.startedTurning=running_time()
        elif self.state==DriveState.TURNING_RIGHT:self.keepTurning(self.RIGHT_LF)
    def turn180(self):
        if self.state==DriveState.READY:
            self.startedTurning=running_time()
            if self.getLinesensorStatus()&self.LEFT_LF:self.linesPassed=0;self.isOnLine=_B
            else:self.linesPassed=1;self.isOnLine=_A
            self.adjustMotors(-self.TURN_TORQUE,self.TURN_TORQUE);self.state=DriveState.TURNING_AROUND
        elif self.state==DriveState.TURNING_AROUND:
            status=self.getLinesensorStatus()
            if status&self.LEFT_LF and running_time()-self.startedTurning>self.EXPECTED_U_TURN_TIME:self.adjustMotors(self.TORQUE,self.TORQUE);self.state=DriveState.FORWARD;radio.send('U: '+str(running_time()-self.startedTurning))
    def driveForward(self):
        if self.state==DriveState.READY:self.state=DriveState.FORWARD
        if self.getLinesensorStatus()&self.LEFT_LF:self.adjustMotors(self.SLOW_TORQUE,self.TORQUE)
        elif self.getLinesensorStatus()&self.RIGHT_LF:self.adjustMotors(self.TORQUE,self.SLOW_TORQUE)
        else:self.adjustMotors(self.TORQUE,self.TORQUE)
    def handleDrive(self,globals):
        if self.state is DriveState.READY:
            if not len(globals.commands):return _A
            command=globals.commands[0];globals.commands=globals.commands[1:]
            if command=='L':self.turnLeft()
            elif command=='R':self.turnRight()
            elif command=='U':self.turn180()
            elif command=='F':self.driveForward()
        elif self.state is DriveState.TURNING_LEFT:self.turnLeft()
        elif self.state is DriveState.TURNING_RIGHT:self.turnRight()
        elif self.state is DriveState.TURNING_AROUND:self.turn180()
        elif self.state is DriveState.FORWARD:self.driveForward()
        return _B
def setLEDs(fireleds,r,g,b,brightness=1.):
    for pixel_id in range(0,11):fireleds[pixel_id]=int(255.*r*brightness),int(255.*g*brightness),int(255.*b*brightness)
    fireleds.show()
def initializeNextRun(globals):
    globals.tags.clear();globals.mostRecentTag=0;globals.isOnTag=_A;globals.mostRecentTagTime=0;globals.commands=''
    while radio.receive_bytes()is not _C:0
    globals.runIsStarted=_A
def prepareForCommandsDownload(pn532,drive,globals):
    pn532.handleRFID(globals);placed=globals.isOnTag and drive.getLinesensorStatus()==0
    if not placed:setLEDs(globals.fireleds,1.,1.,0,.5);return _A
    return globals.isOnTag
def commandsDownload(globals):
    if globals.points!=0:globals.points=0;display.scroll('0',wait=_A,loop=_B)
    globals.commands=radio.receive_bytes()
    if globals.commands is _C or len(globals.commands)==0:setLEDs(globals.fireleds,0,0,1.,.5);return _A
    globals.commands='F'+str(globals.commands,'utf8');return _B
def endRun(globals,drive):setLEDs(globals.fireleds,1.,0,0,.5);drive.stop();radio.send(str(globals.points))
globals=Globals()
radio.config(length=globals.MAX_MSG_LENGTH,channel=14,power=7,address=1737826846)
radio.on()
display.on()
pn532=PN532(i2c)
drive=Drive()
while _B:
    initializeNextRun(globals)
    while not prepareForCommandsDownload(pn532,drive,globals)or not commandsDownload(globals):0
    setLEDs(globals.fireleds,0,0,0,0);globals.runIsStarted=_B;currentGameStartTime=running_time()
    try:
        while _B:
            runningTime=running_time()
            if runningTime>=currentGameStartTime+globals.gameTime:break
            pn532.handleRFID(globals)
            if not drive.handleDrive(globals):break
            if globals.mostRecentTagTime!=0 and runningTime<=globals.mostRecentTagTime+globals.tagDisplayTime:setLEDs(globals.fireleds,0,1.,0,(globals.mostRecentTagTime+globals.tagDisplayTime-runningTime)/globals.tagDisplayTime)
    except Exception:display.show(Image.SKULL)
    endRun(globals,drive);sleep(5000)