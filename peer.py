# Operations
# Get a port from the OS
# Connect to server port, get table
#   For each peer, send an offer. If igven request, send files
#   If given an offer, send a request & save files, send ack
# Keep listening for new offers

import socket
import sys
import struct

MAX_BUFFER = 5120
INT_SIZE = 4

server_address = ("localhost", 8000)

this_port = int(sys.argv[1])

# Get peer list from server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(server_address)
client.send(struct.pack('>I',this_port))

port_bytes = client.recv(MAX_BUFFER)
ports : list[int] = []
print(port_bytes,len(port_bytes))

# Skip first return (only sent to ensure the server returns bytes)
for i in range(INT_SIZE, len(port_bytes), INT_SIZE):
    (next_int,) = struct.unpack('>I', port_bytes[i:i+INT_SIZE])
    ports.append(next_int)





'''
exMessage = "Hello world"
byteMessage = str.encode(exMessage)
buffer_size = 5120

soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)


soc.sendto(byteMessage, server_address)

response = soc.recvfrom(buffer_size)
pr = "Response: {}".format(response[0])
print(pr)'''