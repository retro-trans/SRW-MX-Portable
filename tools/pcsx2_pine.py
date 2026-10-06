"""Small client for PCSX2's documented PINE memory/debugging protocol.

Use a dedicated test-profile port, never an unverified user's live instance.
Protocol reference: PCSX2 pcsx2/PINE.cpp, IPCCommand and ParseCommand.
"""
import socket
import struct


class Pine:
    def __init__(self,port):
        self.socket=socket.create_connection(('127.0.0.1',port),timeout=5)
        self.socket.settimeout(10)

    def __enter__(self):return self
    def __exit__(self,*args):self.socket.close()

    def _receive(self,count):
        data=bytearray()
        while len(data)<count:
            chunk=self.socket.recv(count-len(data))
            if not chunk:raise ConnectionError('PINE disconnected')
            data.extend(chunk)
        return bytes(data)

    def call(self,payload):
        self.socket.sendall(struct.pack('<I',len(payload)+4)+payload)
        size=struct.unpack('<I',self._receive(4))[0]
        if not 5<=size<=450000:raise ValueError('Unexpected PINE packet size')
        response=self._receive(size-4)
        if response[0]!=0:raise RuntimeError('PINE command failed')
        return response[1:]

    def read(self,address,length):
        output=bytearray()
        for begin in range(0,length,65536):
            count=min(length-begin,65536);full=count//8;tail=count%8
            payload=b''.join(b'\x03'+struct.pack('<I',address+begin+n*8) for n in range(full))
            payload+=b''.join(b'\x00'+struct.pack('<I',address+begin+full*8+n) for n in range(tail))
            result=self.call(payload)
            if len(result)!=count:raise ValueError('Short memory response')
            output.extend(result)
        return bytes(output)

    def string(self,command):
        result=self.call(bytes([command]));size=struct.unpack_from('<I',result)[0]
        return result[4:4+size].rstrip(b'\0').decode('utf8')

    def status(self):return struct.unpack('<I',self.call(b'\x0f'))[0]
