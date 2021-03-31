# Naman Balbir Singh Makkar
# s1893731

import sys
import socket
import math
import time
import _thread
import threading
import signal
from threading import Timer
import os

class Sender4():
    def __init__(self):
        self.ip = sys.argv[1] # UDP IP address
        self.port = int(sys.argv[2]) # Port
        self.filename = sys.argv[3]  # Filename to be sent 
        self.retry_timeout = int(sys.argv[4]) # Timeout in ms
        self.windowSize = int(sys.argv[5])
        self.address = (self.ip,self.port) # Setting up the address to send packets to
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Setting up the socket to send the file
        self.sock.settimeout(self.retry_timeout/1000)
        self.payload = 1024 # Payload length of 1024
        self.start = 0  # Start byte, to be incremented by 1024 everytime a packet is sent
        self.EOF = 0    # EOF byte - 3rd byte for the header
        self.seq = 0    # Sequence number incremented by one for each packet sent
        self.fileByteArray = self.generate_byte_array() # Generates a bytearray of the file to be sent
        self.maxFullPackets = math.ceil(len(self.fileByteArray)/self.payload) - 1 # The maximum number of full packets we can get 
        self.fullPktCount = 0 # The counter for number of full packets
        self.ackData = None   # The ackData - what we receive as ack
        self.finalPacket = len(self.fileByteArray) % self.payload # final packet in case of overflow
        self.base = 1 # Base in a window
        self.lastWindowPacket = 0  # Last packet in the window
        self.totalPackets = self.calcTotalPackets() # Total Number of packets, including the final packet in case of overflow 
        self.finalSeqNum = math.ceil(float(len(self.fileByteArray))/float(self.payload)) # The final sequence number - Max val seq can take
        self.nextSeqNum = 1 # The next packet to be sent - Used in Go back N to resend packet when ACK is not received
        self.lock = threading.Lock() # Used for locking threads
        self.listAcked = set() # The list of packets which have been acked
        self.sentNotAcked = [] # The list of packets which have been sent but not acked
        self.lastAck = -1 # The last ack sent
        self.packets = [] # The list of packets to be sent
        self.start_time = 0 # The start time of the file transfer
        self.end_time = 0 # The end time of the file transfer

    def get_throughput(self,time_start,time_end):
        ''' Calculates the throughput for the file transfer '''
        return (len(self.fileByteArray)/self.payload)/(time_end - time_start)

    def generate_byte_array(self):
        ''' Generates a byte array of the file that is to be sent '''
        f = open(self.filename,'rb')
        fileData = f.read()
        fileByteArray = bytearray(fileData)
        f.close()
        return fileByteArray

    def calcTotalPackets(self):
        ''' Calculates the total Number of Packets '''
        if(bool(self.finalPacket)):
            return self.maxFullPackets + 1
        return self.maxFullPackets 

    def store_packets(self):
        ''' Function used for appending packets to the list of packets '''
        if self.seq == self.finalSeqNum:
            self.EOF = 1
        firstTwoHeaderBytes = self.seq.to_bytes(2,'big')
        packet = bytearray(firstTwoHeaderBytes)
        packet.append(self.EOF)
        packet.extend(self.fileByteArray[self.start:(self.start+self.payload)])
        self.start += self.payload
        return packet

    def find_next_acked(self):
        ''' Finds the next packet to be acked '''
        next_ack = self.lastAck + 1
        while next_ack in self.listAcked:
            next_ack += 1
        return next_ack - 1

    def retransmission(self):
        ''' Removes the oldest packet from sentNotAcked so it is retransmitted '''
        if len(self.sentNotAcked) > 0:
            self.sentNotAcked.pop(0)

    def ack_handler(self):
        ''' Thread for handling acks '''
        try:
            self.ackData = self.sock.recvfrom(2)
            ackSeqNum = int.from_bytes(self.ackData[0][:2],'big')
            with self.lock:
                self.listAcked.add(ackSeqNum)
                self.sentNotAcked.remove(ackSeqNum)
                self.lastAck = self.find_next_acked()
        except:
            with self.lock:
                self.retransmission()

    def map_packet_to_ack(self):
        ''' Maps the packet to the ACK received by the packet '''
        self.packetACKs = dict(zip(self.packets,self.listAcked))
        
    def send_file(self):
        ''' Uses the ack_handler function as a thread '''
        self.lastAck = -1
        while self.fullPktCount < self.totalPackets:
            self.packets.append(self.store_packets())
            self.seq += 1
            self.fullPktCount += 1

        self.start_time = time.perf_counter()

        while True:
            if (len(self.packets) == len(self.listAcked)):
                break
            for pktInWindow in range(self.lastAck + 1, self.lastAck + self.windowSize + 1):
                if (pktInWindow in self.listAcked) or (pktInWindow in self.sentNotAcked) or (pktInWindow >= len(self.packets)):
                    continue
                else:
                    self.sock.sendto(self.packets[pktInWindow],self.address)        
                    with self.lock:
                        self.sentNotAcked.append(pktInWindow)
                    ack_handler_thread = threading.Thread(target=self.ack_handler, args=()).start()

        self.end_time = time.perf_counter()

              
if __name__ == '__main__':
    sender = Sender4()
    sender.send_file()
    time_start = sender.start_time
    time_end = sender.end_time
    throughput = sender.get_throughput(time_start,time_end)
    print(f'Throughput is {throughput}')
    print(f'Image : {sender.filename} sent')