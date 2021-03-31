# Naman Balbir Singh Makkar
# s1893731

import sys
import socket

class Receiver2():
    def __init__(self):
        self.port = int(sys.argv[1])
        self.ip = "localhost"
        self.filename = sys.argv[2]
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.bind((self.ip,self.port)) # Accepting packets on this socket
        self.newFile = bytearray() # The new file that is to be saved
        self.data = None
        self.prevSeq = 0 # Send ACKs with the help of sequence numbers
        self.currSeq = 0
        self.BUFFER_SIZE = 1027
        self.EOF = 0
    
    def create_newfile(self):
        ''' Writes to the new file to be saved '''
        with open(self.filename, 'wb') as f:
            f.write(self.newFile)
        
    def update_newfile_bytearray(self):
        ''' Updates the newFile bytearray with the packets from the sender 
            Sends ACKs on receiving packets'''
        while True:

            self.data,addr = self.sock.recvfrom(self.BUFFER_SIZE)
            self.currSeq = int.from_bytes(self.data[:2],'big')
        
            if (self.currSeq == self.prevSeq + 1):
                self.prevSeq = self.currSeq
                self.newFile.extend(self.data[3:])

                ack = bytearray(self.prevSeq.to_bytes(2,'big'))
                self.sock.sendto(ack, addr)

            else:
                ack = bytearray(self.prevSeq.to_bytes(2,'big'))
                self.sock.sendto(ack, addr)

            if (self.data[2] == 1):
                seq = 0
                ack = bytearray(seq.to_bytes(2,'big'))
                self.sock.sendto(ack, addr)
                break
                

if __name__ == '__main__':
    receiver = Receiver2()
    receiver.update_newfile_bytearray()
    receiver.create_newfile()
    receiver.sock.close()
    print(f'File Downloaded {receiver.filename}')