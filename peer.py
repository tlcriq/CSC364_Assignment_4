# Details in README

import socket
import sys
import struct
import os
from threading import Thread


MAX_BUFFER = 5120
PEER_ID_SIZE = 36
PORT_SIZE = 4
F_NAME_SIZE = 32
MAX_CHUNK_SIZE = 64
CHUNK_FORMAT = '64s'

server_address = ("localhost", 8000)

this_ip = sys.argv[1]
this_port = int(sys.argv[2])
this_direct = "directories/"+sys.argv[3]

# Get peer list from server
ssoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssoc.connect(server_address)
peerID = struct.pack('>I',this_port) + struct.pack('32s', str.encode(this_ip))
ssoc.send(peerID)

address_bytes = ssoc.recv(MAX_BUFFER)
addresses : list[tuple[str, int]] = []

# Skip first return (only sent to ensure the server returns bytes)
for i in range(PEER_ID_SIZE, len(address_bytes), PEER_ID_SIZE):
    (next_port,) = struct.unpack('>I', address_bytes[i:i+PORT_SIZE])
    (next_ip,) = struct.unpack('32s', address_bytes[i+PORT_SIZE:i+PEER_ID_SIZE])
    next_ip = next_ip.decode().rstrip("\x00")
    addresses.append((next_port, next_ip))

print("Recieved addresses:", addresses)


# Read in files, get tuples of name and file contents
files : dict[str, str] = {}
for filename in os.listdir(this_direct):
    path = os.path.join(this_direct, filename)
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            files[filename] = f.read()

# listening thread may recieve
# sending can be offer, transfer, or request
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    soc.bind(("localhost", this_port))
except:
    print("Bind failed. Error : " + str(sys.exc_info()))
    sys.exit()
soc.listen()

# Small helper function (T messages)
#def transfer_chunk(connection : socket.socket, chunk : str):


# Thread for offering and sending files to a single peer
# Fortunately TCP should handle retransmissions of lost chunks
def offer_files(connection : socket.socket, files : dict[str,str], peerID : bytes):
    for file in files:
        # Send offer
        offer : bytes = b'O' + peerID
        offer += struct.pack('32s', file)
        connection.send(offer)

        req = connection.recv(1+F_NAME_SIZE).decode().rstrip('\x00')
        if not req:
            break
        if req[0] == 'R':
            if file == req[1:]:
                send = ""
                if(len(file)>MAX_CHUNK_SIZE):
                    send = file[:MAX_CHUNK_SIZE]
                    file = file[MAX_CHUNK_SIZE:]
                else:
                    send = file
                connection.send(b'T' + struct.pack(CHUNK_FORMAT, send))

                while len(file) > MAX_CHUNK_SIZE:
                    ack = connection.recv(1+PEER_ID_SIZE).decode().rstrip('\x00')
                    if ack[0] == 'A':
                        if ack[1:]==peerID.decode():
                            connection.send(b'T' + struct.pack(CHUNK_FORMAT, file[:MAX_CHUNK_SIZE]))
                            file = file[MAX_CHUNK_SIZE:]

                        else:
                            print("Unexpected ack from peer ", peerID.decode())
                    else:
                        print("Unusual request:",req[0],req[1:])
                # Final transmission
                ack = connection.recv(1+PEER_ID_SIZE).decode().rstrip('\x00')
                if ack[0] == 'A' and ack[1:]==peerID.decode():
                    connection.send(b'F' + struct.pack(CHUNK_FORMAT, file))
            else:
                print(f"Request for unexpected file {req[1:]} from {peerID.decode()}")
    print("Finished sending to peer", peerID)


# Server part of peer
def recieve_files(connection : socket.socket, files : dict[str,str], peerID : bytes):
    # Expect transfers. Get final. Expect more offers

    print("recieving")


# Offer to the peers
for address in addresses:
    peer_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        peer_soc.connect(address)
    except:
        print("Connection Error to", address)
        sys.exit()

    try:
        thd = Thread(target=offer_files, args=(peer_soc, files.copy(), peerID))
        thd.start()
    except:
        print("Thread did not start.")
        sys.exit()


# While loop
# If you recieve an offer, check you do not have the file, then thread to accept
while True:
    conn, addr = soc.accept()
    msg_type = conn.recv(1, socket.MSG_PEEK)
    if msg_type==b'O':
        print("start file-accepting thread")
    else:
        print("Unexpected message type:", msg_type.decode())

'''
exMessage = "Hello world"
byteMessage = str.encode(exMessage)
buffer_size = 5120

soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)


soc.sendto(byteMessage, server_address)

response = soc.recvfrom(buffer_size)
pr = "Response: {}".format(response[0])
print(pr)'''