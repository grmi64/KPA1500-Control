"""Independent implementation of Elecraft's published KPA1500 command protocol.
Reference: https://ftp.elecraft.com/KPA1500/Manuals%20Downloads/KPA1500ProgrammingReferenceV3.pdf
No QK4 source is incorporated. SET commands are allow-listed and verified, never replayed.
"""
import re,time,math
BANDS=['160m','80m','60m','40m','30m','20m','17m','15m','12m','10m','6m']
FAULTS={'00':'No active fault','10':'Controller watchdog reset','20':'PA current high','40':'PA temperature high — allow cooling','60':'Input power high','61':'Gain low','70':'Frequency outside supported range','80':'50 V supply out of range','81':'5 V supply out of range','82':'10 V supply out of range','83':'12 V supply out of range','84':'Negative supply out of range','85':'LPF board supply missing','90':'Reflected power high','91':'Very high SWR','92':'ATU could not find a match','B0':'Dissipation high','C0':'Forward power high','C1':'Power exceeds ATU setting limit','F0':'Gain high'}
FAST=('VG','PWF','PWR','SW','TM','OS','FL','TP','AN','AM','AI')
SLOW=('BN','FR','PWI','PC','VI','SB','DS')
class Protocol:
 def __init__(self,transport):self.transport=transport;self.buffer=b'';self.log=[]
 def send(self,command):
  if not re.fullmatch(r'\^[A-Z0-9+]+;',command):raise ValueError('Invalid command.')
  self.transport.write(command.encode('ascii'));self.log=(self.log+[command])[-40:]
 def query(self,tag,timeout=.25):
  self.send('^'+tag+';');deadline=time.monotonic()+timeout
  while time.monotonic()<deadline:
   while b';' in self.buffer:
    frame,self.buffer=self.buffer.split(b';',1)
    text=frame.decode('ascii',errors='strict').strip()
    if text.upper().startswith('^'+tag) or (tag=='I' and text.upper()=='^KPA1500'):return text+';'
    if text in ('?','^?'):raise ValueError('Command not supported: '+tag)
   self.buffer+=self.transport.read(min(.05,max(0,deadline-time.monotonic())))
   if len(self.buffer)>4096:raise ValueError('Invalid oversized amplifier response.')
  raise TimeoutError('No response to '+tag)

def parse(frame):
 text=frame.strip()
 if not text.startswith('^') or not text.endswith(';'):raise ValueError('Invalid amplifier frame.')
 body=text[1:-1];result={}
 def number(prefix,maximum):
  raw=body[len(prefix):].strip()
  if not re.fullmatch(r'\d+(?:\.\d+)?',raw):raise ValueError('Invalid '+prefix+' response.')
  value=float(raw)
  if not math.isfinite(value) or not 0<=value<=maximum:raise ValueError('Out-of-range '+prefix+' response.')
  return value
 for tag,key,maximum in [('PWF','forward_watts',20000),('PWR','reflected_watts',20000),('PWI','input_watts',2000),('TM','temperature_c',200),('PC','current_a',300),('FR','frequency_khz',100000),('SW','swr',999),('SB','bypass_swr',999)]:
  if body.startswith(tag):
   value=number(tag,maximum);return {key:value/10 if tag in ('SW','SB') else value}
 if re.fullmatch(r'OS[01]',body):return {'operate':body[2]=='1'}
 if re.fullmatch(r'TP[01]',body):return {'tuning':body[2]=='1'}
 if re.fullmatch(r'AI[01]',body):return {'atu_inline':body[2]=='1'}
 if body in ('AMI','AMB'):return {'atu_enabled':body[2]=='I'}
 if re.fullmatch(r'AN\d{1,2}',body) and 1<=int(body[2:])<=32:return {'antenna':int(body[2:])}
 if re.fullmatch(r'BN\d{1,2}',body) and int(body[2:])<len(BANDS):return {'band':BANDS[int(body[2:])]}
 if re.fullmatch(r'FL[0-9A-Fa-f]{2}',body):
  code=body[2:].upper();return {'fault_code':code,'fault':FAULTS.get(code,'Amplifier fault '+code)}
 if body.startswith('VI'):
  match=re.fullmatch(r'VI\s*(\d{1,4})\s+(\d{1,3})',body)
  if match:return {'voltage_v':int(match[1])/10,'current_a':int(match[2])}
 if body.startswith('VG'):
  key=re.search(r'KeyIn:([01])\b',body)
  if 'TR_STATE_TX' in body or (key and key[1]=='1') or '3T:1' in body:return {'transmitting':True,'tr_state':body[2:].strip()}
  receiving=bool(re.search(r'\bTR_STATE_RX\b',body))
  standby_idle=all(re.search(pattern,body) for pattern in (r'\bTR_STATE_PA_BYPASSED_3R_ON\b',r'\b3R:1\b',r'\b3T:0\b',r'\bBias:0\b',r'\bPA STBY\b',r'\bMODE_STBY\b'))
  if key and key[1]=='0' and (receiving or standby_idle):return {'transmitting':False,'tr_state':body[2:].strip()}
  return {'transmitting':None,'tr_state':body[2:].strip()}
 if body.startswith('SN'):return {'serial':body[2:][:32]}
 if body.startswith('RVM'):return {'firmware':body[3:][:32]}
 if body.startswith('DS'):return {'lcd':body[2:][:80]}
 raise ValueError('Unsupported or malformed response.')

class Session:
 def __init__(self,transport,cancelled=lambda:False):self.cancelled=cancelled;self.protocol=Protocol(transport);self.values={};self.observed={};self.errors={};self.last_live=0
 def read(self,tag):
  try:
   values=parse(self.protocol.query(tag));stamp=time.time();self.values.update(values);self.observed.update({k:stamp for k in values});self.errors.pop(tag,None)
   if tag=='PWF':self.last_live=stamp
   return values
  except (ValueError,TimeoutError,UnicodeError) as exc:self.errors[tag]=str(exc);return {}
 def identify(self):
  for _ in range(3):
   try:
    if self.protocol.query('I',.6).upper()=='^KPA1500;':
     self.read('SN');self.read('RVM');return
   except TimeoutError:pass
  raise ValueError('This port did not identify as a KPA1500. Check Host PC USB and baud rate.')
 def poll(self,slow=False):
  for tag in FAST+(SLOW if slow else ()):self.read(tag)
 def snapshot(self):
  now=time.time();age=now-self.last_live if self.last_live else None
  values={k:(v if now-self.observed.get(k,0)<(12 if k in ('serial','firmware','band','frequency_khz','input_watts','current_a','voltage_v','bypass_swr','lcd') else 3) or k in ('serial','firmware') else None) for k,v in self.values.items()}
  live=age is not None and age<2.5
  if not live:
   for k in ('forward_watts','reflected_watts','swr','temperature_c','input_watts','current_a','voltage_v'):values[k]=None
  return dict(values,status='live' if live else 'stale',age_seconds=age,errors=dict(self.errors))
 def action(self,name):
  # Query the amplifier again immediately before writes; never trust a screen's old TX state.
  choices={'operate':('^OS1;','OS','operate',True),'standby':('^OS0;','OS','operate',False),'antenna_1':('^AN1;','AN','antenna',1),'antenna_2':('^AN2;','AN','antenna',2),'antenna_next':('^AN0;','AN','antenna',None),'atu_in':('^AMI;','AM','atu_enabled',True),'atu_bypass':('^AMB;','AM','atu_enabled',False),'clear_fault':('^FLC;','FL','fault_code','00'),'tune':('^FT;','TP','tuning',True),'cancel_tune':('^FE;','TP','tuning',False)}
  if name not in choices:raise ValueError('Unknown operating control.')
  required=('VG','PWF','TP','FL','OS','AM')
  for tag in required:
   if not self.read(tag):raise ValueError('Cannot verify amplifier status; control was not sent.')
  state=self.snapshot()
  if state['status']!='live':raise ValueError('Live amplifier status required.')
  if name!='cancel_tune':
   if state.get('transmitting') is not False or state.get('forward_watts',1)>.5:raise ValueError('Blocked while transmitting or RF is present. Release transmit and try again.')
   if state.get('tuning'):raise ValueError('ATU tune is active. Cancel or wait for it to finish.')
  if name=='operate' and state.get('fault_code')!='00':raise ValueError('Review and clear the amplifier fault before selecting Operate.')
  if name=='tune' and (state.get('fault_code')!='00' or state.get('atu_enabled') is not True):raise ValueError('Clear faults and enable the ATU before starting a tune.')
  command,tag,key,expected=choices[name]
  if self.cancelled():raise ValueError('Connection is closing; control was not sent.')
  self.protocol.send(command)
  # A setter may echo the same tag. Readback is the amplifier's actual reported state.
  self.read(tag);reported=self.values.get(key)
  if tag in self.errors or (expected is not None and reported!=expected):
   return {'status':'unconfirmed','message':'Command sent once; expected state was not confirmed. Check the amplifier.','action':name}
  return {'status':'confirmed','message':('Antenna '+str(reported)+' reported.' if name=='antenna_next' else name.replace('_',' ').capitalize()+' confirmed.'),'action':name}
