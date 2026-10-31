"""Read local route configuration; no packets, probes or routed targets."""
import ipaddress,json,os,subprocess
from pathlib import Path

def targets_from_records(records):
 if isinstance(records,dict):records=[records]
 if not isinstance(records,list) or len(records)>64:raise ValueError('Invalid local interface data.')
 valid=[]
 for item in records:
  try:
   address=ipaddress.IPv4Address(item['address']);prefix=item['prefix'];gateway=ipaddress.IPv4Address(item['gateway']);metric=item['metric']
   if type(prefix) is not int or not 1<=prefix<=30 or type(metric) is not int or metric<0:continue
   if any((address.is_loopback,address.is_unspecified,address.is_multicast,address.is_link_local)):continue
   network=ipaddress.IPv4Network(f'{address}/{prefix}',strict=False)
   if gateway not in network or gateway in (network.network_address,network.broadcast_address,address):continue
   if prefix<24:network=ipaddress.IPv4Network(f'{address}/24',strict=False)
   valid.append((metric,int(address),address,network))
  except (KeyError,TypeError,ValueError):continue
 if not valid:raise ValueError('No directly attached IPv4 default interface found. Use manual IP settings.')
 _,_,address,network=min(valid)
 return [str(host) for host in network.hosts() if host!=address]

def read_records():
 # Fixed code and no interpolated user input. PowerShell reads configuration only.
 script="""$ErrorActionPreference='Stop'; $records=@(); foreach($route in (Get-NetRoute -AddressFamily IPv4 | Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' })) { foreach($ip in (Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.InterfaceIndex | Where-Object { $_.AddressState -eq 'Preferred' -and -not $_.SkipAsSource })) { $records += @{address=$ip.IPAddress;prefix=[int]$ip.PrefixLength;gateway=$route.NextHop;metric=[int]($route.RouteMetric+$route.InterfaceMetric)} } }; ConvertTo-Json -Compress -InputObject @($records)"""
 shell=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
 result=subprocess.run([str(shell),'-NoProfile','-NonInteractive','-Command',script],stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',timeout=15,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 if len(result.stdout)>65536:raise ValueError('Oversized interface data.')
 return json.loads(result.stdout)

def local_targets():
 return targets_from_records(read_records())
