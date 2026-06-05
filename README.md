System design:

Server tracks peers which register with it, allowing it to send a list of all peers on the network whenever a new one connects.

The peer's ID is its IP and port

To add a peer, provide the ip, port, and associated directory as command-line arguments.

The peer will send offers of its own files to all other peers.

MESSAGE CODES:
O - Offer
R - Request
T - Transfer
F - Final (New - used to signify this is the last chunk)
A - Ack

Message codes do not use a peer ID as 