"""In-process, explicitly labelled demonstration transport. Never opens devices or sockets."""
import time
class SimulatorTransport:
 def __init__(self):self.buffer=b'';self.power=True;self.operate=False;self.antenna=1;self.atu=True;self.tx=False;self.fault='00';self.tune_until=0;self.writes=[];self.closed=False
 def write(self,data):
  command=data.decode();self.writes.append(command);tag=command[1:-1];answer=None
  if tag=='ON1':self.power=True
  elif tag=='ON0':self.power=False
  elif tag=='I':answer='^KPA1500;'
  elif tag=='OS1':self.operate=True
  elif tag=='OS0':self.operate=False
  elif tag in ('AN1','AN2'):self.antenna=int(tag[-1])
  elif tag=='AN0':self.antenna=3-self.antenna
  elif tag=='AMI':self.atu=True
  elif tag=='AMB':self.atu=False
  elif tag=='FLC':
   if self.fault!='40':self.fault='00'
  elif tag=='FT':self.tune_until=time.monotonic()+4
  elif tag=='FE':self.tune_until=0
  else:
   tuning=time.monotonic()<self.tune_until
   replies={'ON':str(int(self.power)),'MA':'54:10:EC:14:75:22','WL':'1','SN':'DEMO-ONLY','RVM':'03.03','VG':' TR_STATE_TX 3R:0 3T:1 Bias:1 KeyIn:1' if self.tx else ' TR_STATE_RX 3R:1 3T:0 Bias:0 KeyIn:0','PWF':'800' if self.tx else '0','PWR':'4' if self.tx else '0','PWI':'24' if self.tx else '0','SW':'12','SB':'24','TM':'45','PC':'23' if self.tx else '0','VI':'513 '+('023' if self.tx else '000'),'OS':str(int(self.operate)),'TP':str(int(tuning)),'FL':self.fault,'AN':str(self.antenna),'AM':'I' if self.atu else 'B','AI':str(int(self.atu)),'BN':'05','FR':'14080','DS':'14 MHz  45C\n'+('OPER' if self.operate else 'STBY')+'   DEMO'}
   if tag in replies:answer='^'+tag+replies[tag]+';'
  if answer:self.buffer+=answer.encode()
 def read(self,timeout):
  if self.buffer:data=self.buffer;self.buffer=b'';return data
  time.sleep(min(timeout,.01));return b''
 def close(self):self.closed=True
