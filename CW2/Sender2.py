# Naman Balbir Singh Makkar
# s1893731

import sys
import socket
import math
import time

class Sender2():
    def __init__(self):
        self.ip = sys.argv[1] # UDP IP address
        self.port = int(sys.argv[2]) # Port
        self.filename = sys.argv[3]  # Filename to be sent 
        self.retry_timeout = float(sys.argv[4])   # Timeout in ms
        self.address = (self.ip,self.port) # Setting up the address to send packets to
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Setting up the socket to send the file
        self.payload = 1024 # Payload length of 1024
        self.start = 0  # Start byte, to be incremented by 1024 everytime a packet is sent
        self.EOF = 0    # EOF byte - 3rd byte for the header
        self.seq = 0    # Sequence number incremented by one for each packet sent
        self.fileByteArray = self.generate_byte_array() # Generates a bytearray of the file to be sent
        self.maxFullPackets = math.ceil(len(self.fileByteArray)/self.payload) - 1 # The maximum number of full packets we can get 
        self.fullPktCount = 0 # The counter for number of full packets
        self.ackData = None   # The ackData - what we receive as ack
        self.finalPacket = len(self.fileByteArray) % self.payload # final packet in case of overflow
        self.retransmissions = 0 # Number of packet retransmissions
        self.ackNum = 0

    def generate_byte_array(self):
        ''' Generates a byte array of the file that is to be sent '''
        f = open(self.filename,'rb')
        fileData = f.read()
        fileByteArray = bytearray(fileData)
        f.close()
        return fileByteArray

    def get_throughput(self,time_start,time_end):
        ''' Calculates the throughput for the file transfer '''
        return (len(self.fileByteArray)/self.payload)/(time_end - time_start)

    def wait(self):
        ''' Waits for ACKs returns a timeout if ACK is not sent '''
        try:
            self.sock.settimeout(self.retry_timeout/1000)
            self.ackData = self.sock.recvfrom(2)
            self.ackNum = int.from_bytes(self.ackData[0][:2],'big')
            return True
        except socket.timeout:
            return False

    def send_file(self):
        ''' Sends the file
            All the full packets are sent with the help of the while loop 
            Checks for final packet in an if loop in case of overflow '''
        while self.fullPktCount < self.maxFullPackets:
            if (self.fullPktCount == (self.maxFullPackets - 1)) and (self.finalPacket == 0):
                self.EOF = 1
            packet = bytearray()
            self.seq += 1
            firstTwoHeaderBytes = self.seq.to_bytes(2,'big')
            packet += bytearray(firstTwoHeaderBytes)
            packet.append(self.EOF)
            packet.extend(self.fileByteArray[self.start:(self.start + self.payload)])
            self.sock.sendto(packet,self.address)

            while True:
                if (self.wait() and (self.seq == self.ackNum)):
                    #print(f"ACK received : {self.ackNum}")
                    break
                else:
                    #print("Retransmitted Full Packet")
                    self.sock.sendto(packet,self.address)
                    self.retransmissions += 1
            
            self.start += self.payload
            self.fullPktCount += 1

        if(bool(self.finalPacket)):
            self.seq += 1
            self.EOF += 1
            packet = bytearray()
            firstTwoHeaderBytes = self.seq.to_bytes(2,'big')
            packet += bytearray(firstTwoHeaderBytes)
            packet.append(self.EOF)
            packet.extend(self.fileByteArray[self.start:(self.start + self.finalPacket)])
            self.sock.sendto(packet,self.address)
            #print(f'Sequence Num : {self.seq}')
            #print(f'ACK : {self.ackNum}')
            while True:
                if(self.wait() and (self.ackNum == 0 or self.seq == self.ackNum)):
                    #print(f"ACK received : {self.ackNum}")
                    break
                
                else:
                    #print("Retransmitted Final")
                    self.sock.sendto(packet,self.address)
                    self.retransmissions += 1

if __name__ == '__main__':
    sender = Sender2()
    time_start = time.perf_counter()
    sender.send_file()
    time_end = time.perf_counter()
    throughput = sender.get_throughput(time_start,time_end)
    sender.sock.close()
    print(f'Number of retransmissions = {sender.retransmissions}')
    print(f'Throughput is {throughput}')
    print(f'Image : {sender.filename} sent')