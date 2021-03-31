# Naman Balbir Singh Makkar
# s1893731

import sys
import socket

class Receiver1():
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
            self.data = None
            self.data = self.sock.recvfrom(1027)
            self.newFile.extend(self.data[0][3:])

            if(self.data[0][2] == 1):
                break

if __name__ == "__main__":
    receiver = Receiver1()
    receiver.update_newfile_bytearray()
    receiver.create_newfile()
    receiver.sock.close()
    print(f"File downloaded as {receiver.filename}")