import socket
import os
import json

STORAGE_PATH = os.path.join(".", "users.json")
users = dict()


def load_users(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError as err:
        print(f"Can't load users from {path}: {str(err)}\nNon fatal error. Creating storage")
        with open(path, "w") as f:
            json.dump({}, f)
    except OSError as err:
        raise SystemExit(f"Can't load users from {path}: {str(err)}")
    return {}
        

def register_user(users, username, password):
    with open(STORAGE_PATH, "w") as f:
        # TODO: for now store it as plaintext
        users[username] = password
        json.dump(users, f)


def username_exists(users, username):
    if username in users.values():
        return True
    return False

def format_address(addr):
    return f"{addr[0]}:{addr[1]}"

class ServerCommand:
    REGISTER = "REGISTER"
    LOGIN = "LOGIN"
    SEND = "SEND"
    LOGOUT = "LOGOUT"


users = load_users(STORAGE_PATH)
login_users = []

MAX_BUFFER_SIZE = 4096

localhost = socket.gethostbyname("localhost")
PORT = 1234

sock = socket.socket()

# SOL = Socket Option Level
# SO = Socket Option
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sock.bind((localhost, PORT))
sock.listen()
print("Listening on localhost:1234")

# Let's just do one connection for now
# TODO: support multiple connections
conn, addr = sock.accept()
print(addr)

while True:
    recv = conn.recv(MAX_BUFFER_SIZE)
    recv = recv.decode("utf-8").split(" ")
    command = recv[0]
    if command == ServerCommand.REGISTER:
        if len(recv) < 3:
            conn.send(b"Please provide a username and password\ntry REGISTER myusername password")
            continue
        username = recv[1]
        if username_exists(users, username):
            conn.send(b"username already exists!")
            continue
        password = recv[2]
        register_user(users, username, password)
        conn.send(f"Registered {username}".encode())
    elif command == ServerCommand.LOGIN:
        if len(recv) < 3:
            conn.send(b"Please provide a username and password\ntry LOGIN myusername password")
            continue
        username = recv[1]
        if username in users:
            # For now let's just do this to log client in
            password = recv[2]
            if password == users[username]:
                conn.send(b"Logging in...")
                login_users.append(addr)
            else:
                conn.send(b"Invalid password")
                continue
        else:
            conn.send(b"You need to register first\ntry REGISTER myusername password")
            continue
    elif command == ServerCommand.SEND:
        if addr not in login_users:
            conn.send(b"You need to login.\nTry LOGIN")
            continue
        if len(recv) < 2:
            conn.send(b"You need to provide your message after SEND\ntry SEND i love you")
            continue
        msg = recv[1:]
        # For now just send it back. Will explore broadcast later.
        conn.send(" ".join(msg).encode())
    elif command == ServerCommand.LOGOUT:
        # TODO: Proper logout
        conn.send(b"Logging out...")
        conn.close()
        break
    else:
        conn.send(f"Unknown command {command}".encode())
        # TODO: Send list of command to client
        continue
sock.close()
