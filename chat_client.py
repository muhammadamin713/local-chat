# This client has to be better. It's
# blocking user from sending message if
# the server isn't sending them anything
# It's better to just use netcat

import socket

MAX_BUFFER_SIZE = 4096

localhost = socket.gethostbyname("localhost")
PORT = 1234

sock = socket.socket() 

sock.connect((localhost, PORT))

while True:
	msg = input("Send> ")
	sock.send(msg.encode())
	
	data = sock.recv(MAX_BUFFER_SIZE)
	print(data.decode("utf-8"))
	
	if msg == "LOGOUT":
		break
