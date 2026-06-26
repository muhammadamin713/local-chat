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
