# Naman Balbir Singh Makkar
# s1893731

import sys
import socket
import math
import time
import threading
import _thread

class Sender3(object):
    def __init__(self):
        self.ip = sys.argv[1] # UDP IP address
        self.port = int(sys.argv[2]) # Port
        self.filename = sys.argv[3]  # Filename to be sent 
        self.retry_timeout = int(sys.argv[4]) # Timeout in ms
        self.windowSize = int(sys.argv[5])
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
        self.base = 0 # Base in a window
        self.totalPackets = self.calcTotalPackets() # Total Number of packets, including the final packet in case of overflow 
        self.finalSeqNum = math.ceil(float(len(self.fileByteArray))/float(self.payload)) # The final sequence number - Max val seq can take
        self.nextPacket = 0 # The next packet to be sent - Used in Go back N to resend packet when ACK is not received
        self.lock = threading.Lock() # Used for locking threads
        self.packets = [] # The list of all packets to be sent

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

    def set_window_size(self,numPackets):
        ''' Calculates the window size '''
        return min(self.windowSize, (numPackets - self.base)) 

    def send_packets(self):
        ''' Sends a packet to receiver '''
        if self.seq == self.finalSeqNum:
            self.EOF = 1
        firstTwoHeaderBytes = self.seq.to_bytes(2,'big')
        packet = bytearray(firstTwoHeaderBytes)
        packet.append(self.EOF)
        packet.extend(self.fileByteArray[self.start:(self.start+self.payload)])
        self.start += self.payload
        return packet

    def receive_ack(self):
        ''' Receives the ACK from the receiver 
            Changes the value of the base if the ack is greater than or equal to the base '''
        while True:
            try:
                self.ackData = self.sock.recvfrom(2)
                self.ackNum = int.from_bytes(self.ackData[0][:2],'big')
                if self.ackNum >= self.base:
                    self.lock.acquire()
                    self.base = self.ackNum + 1
                    self.lock.release()
            except socket.error as exception:
                print(f'Caught socket exception {exception}')
            
    def send_file(self):
        ''' Uses the receive_ack function as a thread 
            Socket timeout was not used using the library function socket.settimeout()
            since the thread lock had to be timed simultaneously and that couldn't be done using socket.settimeout, 
            the time library was used for this purpose '''

        while self.fullPktCount < self.totalPackets:
            self.packets.append(self.send_packets())
            self.seq += 1
            self.fullPktCount += 1

        self.windowSize = self.set_window_size(self.totalPackets)
        
        _thread.start_new_thread(self.receive_ack,())
        while self.base < self.totalPackets:
            self.lock.acquire()
            while (self.nextPacket < min((self.base + self.windowSize), self.totalPackets)):
                self.sock.sendto(self.packets[self.nextPacket],self.address)
                self.nextPacket += 1

            start_time = time.perf_counter()   

            while time.perf_counter() < (start_time + self.retry_timeout/1000):
                self.lock.release()
                time.sleep(self.retry_timeout/1000)
                self.lock.acquire()

            if time.perf_counter() >= (start_time + self.retry_timeout/1000):
                start_time = time.perf_counter()
                self.nextPacket = self.base
                self.retransmissions += 1
            else:
                self.windowSize = self.set_window_size(self.totalPackets) 
            self.lock.release()
        self.sock.sendto(bytearray(),self.address)
                
if __name__ == '__main__':
    sender = Sender3()
    time_start = time.perf_counter()
    sender.send_file()
    time_end = time.perf_counter()
    throughput = sender.get_throughput(time_start,time_end)
    sender.sock.close()
    print(f'Number of retransmissions = {sender.retransmissions}')
    print(f'Throughput is {throughput}')
    print(f'Image : {sender.filename} sent')