# Acknowledge new peers
#   Assign an ID
#   Return the table of all peers
# That's pretty much it
import socket
import struct

host = "localhost"
port = 8000

BUFFER_SIZE = 36
PORT_SIZE = 4
soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
soc.bind((host, port))
soc.listen(5)
print("Server started")

addresses : list[bytes] = []

while(True):
    connection, address = soc.accept()
    packet = connection.recv(BUFFER_SIZE)

    (next_port,) = struct.unpack('>I', packet[:PORT_SIZE])
    (next_ip,) = struct.unpack('32s', packet[PORT_SIZE:BUFFER_SIZE])
    print("Connected:", next_ip.decode().rstrip('\x00'), next_port)
    
    bit_table = packet
    for add in addresses:
        bit_table += add
    connection.send(bit_table)
    addresses.append(packet)


