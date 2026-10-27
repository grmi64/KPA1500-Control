"""Exact telemetry-only write boundary. No setters, wake handshake or mixed frames."""
QUERY_TAGS=('VG','PWF','PWR','SW','TM','OS','FL','TP','AN','AM','AI','BN','FR','PWI','PC','VI','SB','DS','FC','FS','ON','MA','WL','I','SN','RVM')
QUERIES=frozenset(('^'+tag+';').encode('ascii') for tag in QUERY_TAGS)
class QueryOnlyTransport:
 def __init__(self,transport):self._transport=transport
 def write(self,data):
  if not isinstance(data,bytes) or data not in QUERIES:raise ValueError('Read-only telemetry: operating, tuning, power and wake commands are blocked.')
  return self._transport.write(data)
 def read(self,timeout):return self._transport.read(timeout)
 def close(self):return self._transport.close()
