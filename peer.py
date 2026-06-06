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
peerIDs : list[bytes] = []

# Skip first return (only sent to ensure the server returns bytes)
for i in range(PEER_ID_SIZE, len(address_bytes), PEER_ID_SIZE):
    peerIDs.append(address_bytes[i:i+PEER_ID_SIZE])

# Read in files, get maps from names to file contents
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

# Small helper function to print IDs
def stringID(peerID : bytes):
    (next_port,) = struct.unpack('>I', peerID[:PORT_SIZE])
    (ip,) = struct.unpack('32s', peerID[PORT_SIZE:PEER_ID_SIZE])
    ip = ip.decode().rstrip()
    return f"({ip}, {str(next_port)})"


# Thread for offering and sending files to a single peer
# Fortunately TCP should handle retransmissions of lost chunks
def offer_files(connection : socket.socket, files : dict[str,str], peerID : bytes, targetID : bytes):
    print("Offer to peer", stringID(targetID))
    if not files:
        connection.send(b'O' + peerID + struct.pack('32s', b''))
    for file in files:
        # Send offer
        offer : bytes = b'O' + peerID
        offer += struct.pack('32s', file.encode())
        connection.send(offer)

        req = connection.recv(1+F_NAME_SIZE).decode().rstrip('\x00')
        if not req:
            break
        if req[0] == 'R':
            if file == req[1:]:
                send = ""
                text = files[file]
                if(len(file)>MAX_CHUNK_SIZE):
                    send = text[:MAX_CHUNK_SIZE]
                    text = text[MAX_CHUNK_SIZE:]
                else:
                    send = text
                connection.send(b'T' + struct.pack(CHUNK_FORMAT, send.encode()))

                while len(text) > MAX_CHUNK_SIZE:
                    ack = connection.recv(1+PEER_ID_SIZE).decode()
                    if ack[0] == 'A':
                        if ack[1:]==targetID.decode():
                            connection.send(b'T' + struct.pack(CHUNK_FORMAT, text[:MAX_CHUNK_SIZE].encode()))
                            text = text[MAX_CHUNK_SIZE:]

                        else:
                            print("Unexpected ack from peer ", stringID(targetID))
                    else:
                        print("Unusual request:",req[0],req[1:])
                # Final transmission
                ack = connection.recv(1+PEER_ID_SIZE).decode()
                if ack[0] == 'A' and ack[1:]==targetID.decode():
                    connection.send(b'E' + struct.pack(CHUNK_FORMAT, text.encode()))
                else:
                    print(f"Unexpected ack from peer {stringID(targetID)}: {ack.encode()}")
            else:
                print(f"Request for unexpected file {req[1:]} from {stringID(targetID)}")
        elif req[0]=='I':
            print("Offer rejected")
            continue
    connection.send(b'F' + peerID)
    print("Finished sending to peer", stringID(targetID),"\n")


# Server part of peer
# Subtle distinction: this one has all the original files, not just a copy
def recieve_files(connection : socket.socket, peerID : bytes, this_direct):
    global files
    # Expect transfers. Get End file. Expect more offers unfil final'
    ended = False
    while not ended:
        offer = connection.recv(1+PEER_ID_SIZE+F_NAME_SIZE)
        senderID = offer[1:1+PEER_ID_SIZE]
        offer = offer.decode()
        if offer[0]=='F' or offer[1+PEER_ID_SIZE:].rstrip('\x00')=="":
            print("Finished recieving files from peer",stringID(senderID),"\n")
            ended = True
            break
        
        elif offer[0]=='O':
            # Send request or ignore if you have the file
            f = offer[1+PEER_ID_SIZE:]
            filename = f.rstrip('\x00')
            if filename in files:
                connection.send(b'I'+filename.encode())
                continue
            connection.send(b'R'+f.encode())
            files[filename] = ""
            while True:
                transfer = connection.recv(1+MAX_CHUNK_SIZE).decode()
                if transfer[0]=='E':
                    chunk = transfer[1:].rstrip('\x00')
                    files[filename] = files[filename] + chunk
                    break
                elif transfer[0]=='T':
                    chunk = transfer[1:]
                    files[filename] = files[filename] + chunk
                    connection.send(b'A'+peerID)
                else:
                    print("Unexpected request instead of transfer:",transfer[0],transfer[1:])
            
            # Write to new file
            path = os.path.join(this_direct, filename)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(files[filename])

        else:
            print(f"Unexpected message (non-offer) of type {offer[0]} from {senderID}")
    
# 
def connect_to_peer(targetID : bytes) -> socket.socket:
    (next_port,) = struct.unpack('>I', targetID[:PORT_SIZE])
    (next_ip,) = struct.unpack('32s', targetID[PORT_SIZE:PEER_ID_SIZE])
    next_ip = next_ip.decode().rstrip("\x00")

    peer_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        peer_soc.connect((next_ip, next_port))
    except:
        print("Connection Error to", (next_ip, next_port))
        sys.exit()
    return peer_soc

# Offer to the peers the server told us about
for targetID in peerIDs:
    peer_soc = connect_to_peer(targetID)

    try:
        thd = Thread(target=offer_files, args=(peer_soc, files.copy(), peerID, targetID))
        thd.start()
    except:
        print("Thread did not start.")
        sys.exit()


# While loop
# If you recieve an offer, thread to accept or reject. If the peer is new, add it and send it an offer
while True:
    conn, addr = soc.accept()
    msg = conn.recv(1, socket.MSG_PEEK)
    msg_type = msg.decode()[0]
    if msg_type=='O':
        newID = conn.recv(1+PEER_ID_SIZE, socket.MSG_PEEK)[1:]
        try:
            thd = Thread(target=recieve_files, args=(conn, peerID, this_direct))
            thd.start()
        except:
            print("Thread did not start.")
            sys.exit()

        if not newID in  peerIDs:
            peerIDs.append(newID)
            new_soc = connect_to_peer(newID)
            print("adding peer", newID)
            try:
                thd = Thread(target=offer_files, args=(new_soc, files.copy(), peerID, newID))
                thd.start()
            except:
                print("Thread did not start.")
                sys.exit()
    else:
        print("Unexpected message type:", msg_type)