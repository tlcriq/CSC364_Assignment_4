# Acknowledge new peers
#   Assign an ID
#   Return the table of all peers
# That's pretty much it
import socket
import struct

host = "localhost"
port = 8000

BUFFER_SIZE = 4
soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
soc.bind((host, port))
soc.listen(5)
print("Server started")

ports : list = []

while(True):
    connection, address = soc.accept()
    packet = connection.recv(BUFFER_SIZE)

    (next_port,) = struct.unpack('>I', packet)
    print(next_port)
    
    bit_table = struct.pack('>I', next_port)
    for p in ports:
        bit_table += struct.pack('>I', p)
    print(bit_table)
    connection.send(bit_table)
    ports.append(next_port)


