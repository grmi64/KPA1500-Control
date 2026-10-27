"""Explicit, one-shot Wake-on-LAN. No automatic startup wake."""
import ipaddress,re,socket,time

def mac_address(value):
 if not isinstance(value,str):raise ValueError('Enter the amplifier MAC address.')
 value=value.strip().replace('-',':').upper()
 if not re.fullmatch(r'(?:[0-9A-F]{2}:){5}[0-9A-F]{2}',value):raise ValueError('Enter a six-byte amplifier MAC address.')
 raw=bytes.fromhex(value.replace(':',''))
 if raw==bytes(6) or raw[0]&1:raise ValueError('Enter the amplifier unicast MAC address.')
 return value

def wake_address(value):
 try:address=ipaddress.IPv4Address(value)
 except (ValueError,TypeError):raise ValueError('Enter an IPv4 LAN broadcast address.') from None
 if address.is_unspecified or address.is_multicast or address.is_loopback:raise ValueError('Enter an IPv4 LAN broadcast address.')
 return str(address)

def wake(mac,broadcast):
 raw=bytes.fromhex(mac_address(mac).replace(':',''));packet=b'\xff'*6+raw*16
 with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
  sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1);sock.settimeout(1);sock.sendto(packet,(wake_address(broadcast),9))

def wake_connect(config,cancelled,connect,wait):
 if cancelled():raise ValueError('Connection is closing; wake was not sent.')
 wake(config['wake_mac'],config['wake_broadcast'])
 deadline=time.monotonic()+15;last_error=None
 while not cancelled():
  try:return connect(config['host'],config['tcp_port'])
  except OSError as exc:
   last_error=exc
   if 'already in use' in str(exc):raise
   if time.monotonic()>=deadline:break
   wait(.5)
 if cancelled():raise ValueError('Connection closed after one wake packet; startup was not confirmed. No automatic retry.')
 raise OSError('Wake packet sent once; amplifier connection was not confirmed. Check NET WAKE on LAN, MAC address, cabling and rear power switch. Broadcast wake normally requires the amplifier LAN or a configured wake relay. Last TCP connection error: '+str(last_error))
