System design:

Server tracks peers which register with it, allowing it to send a list of all peers on the network whenever a new one connects.

The peer's ID is its port and IP
To add a peer, provide the ip, port, and associated directory as command-line arguments.
The peer will send offers of its own files to all other peers registered. Upon recieving an offer, the preexisting peer will accept, then record the existence of the new peer and offer its own files.

ERROR RESISTANCE
The system uses TCP, so packets have a built-in retransfer and checksum implementation. Test cases of empty or no files are accounted for. In this specific protocol, each chunk is withheld until the previous one has been acked. If the peer for some reason stalls, the thread specific to the peer will wait until it gets a response.

Peers will also recognize unusual requests and log them in output. These are handled such that the improper packet can be ignored if the others which the sender gives are valid.

NOTE - Peer IDs are 36 bytes (4-byte port number and 32-byte IP to allow string sending)

MESSAGE CODES:
O - Offer
R - Request
T - Transfer
A - Ack

E - End file (Used to signify this is the last chunk, 'e' + peerID)
F - Finish (Signifies the peer has given out its files, 'f' + peerID + file chunk)
I - Ignore (Reject a peer's offer, 'I' + filename)