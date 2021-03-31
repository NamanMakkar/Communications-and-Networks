# Naman Balbir Singh Makkar
# s1893731

import sys
import socket
import math

ip = sys.argv[1]
port = int(sys.argv[2])
filename = sys.argv[3]
address = (ip,port)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class Sender1():
    def __init__(self):
        self.ip = sys.argv[1]
        self.port = int(sys.argv[2])
        self.filename = sys.argv[3]
        self.address = (self.ip,self.port)
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.payload = 1024
        self.start = 0
        self.EOF = 0
        self.seq = 0
        self.fileByteArray = self.generate_byte_array()
        self.maxFullPackets = math.ceil(len(self.fileByteArray)/self.payload) - 1
        self.fullPktCount = 0
        self.finalPacket = len(self.fileByteArray) % self.payload
        
    def generate_byte_array(self):
        f = open(self.filename, 'rb')
        fileData = f.read()
        fileByteArray = bytearray(fileData)
        f.close()
        return fileByteArray

    def send_file(self):
        while self.fullPktCount < self.maxFullPackets:
            if (self.fullPktCount == self.maxFullPackets - 1) and (self.finalPacket == 0 ):
                self.EOF = 1
            firstTwoHeaderBytes = self.seq.to_bytes(2,'big')
            packet = bytearray(firstTwoHeaderBytes)
            packet.append(self.EOF)
            packet.extend(self.fileByteArray[self.start:(self.start + self.payload)])
            self.sock.sendto(packet,self.address)
            self.start += self.payload
            self.fullPktCount += 1
        
        if (bool(self.finalPacket)):
            self.seq += 1
            self.EOF += 1
            firstTwoHeaderBytes = self.seq.to_bytes(2,'big')
            packet = bytearray(firstTwoHeaderBytes)
            packet.append(self.EOF)
            packet.extend(self.fileByteArray[self.start:(self.start + self.payload)])
            self.sock.sendto(packet,self.address)

if __name__ == "__main__":
    sender = Sender1()
    sender.send_file()
    sender.sock.close()
    print(f'Image : {filename} sent')