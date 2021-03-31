# Naman Balbir Singh Makkar
# s1893731

import socket
import sys
import time
from operator import itemgetter

class Receiver4(object):
    def __init__(self):
        self.port = int(sys.argv[1])
        self.ip = "localhost"
        self.filename = sys.argv[2]
        self.windowSize = int(sys.argv[3])
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.bind((self.ip,self.port)) # Accepting packets on this socket
        self.newFile = dict() # The new file that is to be saved
        self.data = None # The packets taken from socket are stored in data
        self.currSeq = 0 # The current sequence number
        self.nextSeq = 0 # The next sequence number
        self.BUFFER_SIZE = 1027 # The payload
        self.EOF = 0 # The EOF flag
        self.recv_last = False 
        self.recv_buffer = set() # Receiver Buffer 
        self.address = None # The address to send the ACKs to
        self.fileAdd = None # Writes to the new filw
        self.finalPacket = None # The last packet
    
    def create_newfile(self):
        ''' Writes to the new file to be saved '''
        for i in range(len(self.newFile)):
            self.fileAdd += self.newFile[i]
        with open(self.filename, 'wb') as f:
            f.write(self.fileAdd)

    def find_next_seq_num(self,seqnum):
        ''' Finds the next sequence number '''
        nextseqnum = seqnum + 1
        while nextseqnum in self.recv_buffer:
            nextseqnum += 1
        return nextseqnum

    def update_newfile_bytearray(self):
        ''' Updates the newFile bytearray with the packets from the sender 
            Sends ACKs on receiving packets'''
        while True:

            self.data,addr = self.sock.recvfrom(self.BUFFER_SIZE)
            self.currSeq = int.from_bytes(self.data[:2],'big')
            self.address = addr
            

            if self.currSeq < self.nextSeq + self.windowSize:
                ack = bytearray(self.currSeq.to_bytes(2,'big'))
                self.sock.sendto(ack,self.address)
                if self.currSeq not in self.recv_buffer:
                    self.newFile[self.currSeq] = bytearray(list(self.data[3:]))
                    self.recv_buffer.add(self.currSeq)
                self.nextSeq = self.find_next_seq_num(self.currSeq)

            if (self.data[2] == 1):
                self.recv_last = True
                self.finalPacket = max(self.newFile.keys())
                break
                
    def ack_last_window(self):
        ''' Sends acks for last window
            Sends it 5 times to account for lost acks '''
        for ack in range(10):
            for idx in range(self.finalPacket, self.finalPacket-self.windowSize, -1):
                self.sock.sendto(bytearray(idx.to_bytes(2,'big')))

if __name__ == '__main__':
    receiver = Receiver4()
    receiver.update_newfile_bytearray()
    receiver.ack_last_window()
    receiver.create_newfile()
    print(f'File Downloaded {receiver.filename}')