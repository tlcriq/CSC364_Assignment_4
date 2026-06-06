System design:

Server tracks peers which register with it, allowing it to send a list of all peers on the network whenever a new one connects.

The peer's ID is its IP and port

To add a peer, provide the ip, port, and associated directory as command-line arguments.

The peer will send offers of its own files to all other peers.

NOTE - Peer IDs are 36 bytes (4-byte port # and 32-byte ID)

MESSAGE CODES:
O - Offer
R - Request
T - Transfer
A - Ack

E - End file (Used to signify this is the last chunk, 'e' + peerID)
F - Finish (Signifies the peer has given out its files, 'f' + peerID)
I - Ignore (Reject a peer's offer)

Message codes do not use a peer ID as 