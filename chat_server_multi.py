import asyncio
import json
import os

HOST = "127.0.0.1"
PORT = 1234

active_users = dict()
STORAGE_PATH = os.path.join(".", "users.json")

def load_users():
    users = {}
    try:
        with open(STORAGE_PATH, "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        with open(STORAGE_PATH, "w") as f:
            json.dump({}, f)
    except OSError as err:
        print(f"Failed to load users: {str(err)}")
    return users

def store_user(username, password):
    users = load_users()
    # store as plain text for this case. Nobody cares. Everything is local
    users[username] = password
    try:
        with open(STORAGE_PATH, "w") as f:
            json.dump(users, f)
    except OSError as err:
        print(f"Can't store users: {str(err)}")
        return False
    return True

def username_exists(username):
    users = load_users()
    if username in users.keys():
        return True
    return False

def authenticate(username, password):
    users = load_users()
    if username in users:
        return users[username] == password

class ServerCommand:
    REGISTER = "REGISTER"
    LOGIN = "LOGIN"
    SEND = "SEND"

async def broadcast(message, cw, skip_owner=True):  
    for user in list(active_users):
        if skip_owner and user == cw:
            continue
        try:
            user.write(message.encode())
            await user.drain()
        except Exception:
            del active_users[cw]

def write_help(cw):
    cw.write(b"Available command\n")
    cw.write(b"-  REGISTER username password\n")
    cw.write(b"-  LOGIN username password\n")
    cw.write(b"-  SEND my message is here\n")

async def client_connected_cb(cr, cw):
    addr = cw.get_extra_info("peername")
    print(f"[*] New connection established from {addr}")

    try:
        while True:
            data = await cr.read(4096)
            
            if not data:
                print(f"[*] Client {addr} closed the connection.")
                if cw in active_users:
                    await broadcast(f"{active_users[cw]['username']} leave the chat room\n", cw)
                break
            
            message = data.decode("utf-8").strip().split(" ")
            if len(message) < 1:
                cw.write(b"Please enter a command\n")
                continue
            command = message[0]
            if command == ServerCommand.REGISTER:
                if len(message) < 3:
                    cw.write(b"try REGISTER username password\n")
                    continue
                username = message[1]
                if username_exists(username):
                    cw.write(f"The username {username} already exists\n".encode())
                    continue
                password = message[2]
                if not store_user(username, password):
                    cw.write(b"Failed to store users in database\n")
                    cw.write(b"You can still use the username\n")
                    cw.write(b"But next time you have to REGISTER a username once you quit\n")
            elif command == ServerCommand.LOGIN:
                if len(message) < 3:
                    cw.write(b"try LOGIN username password\n")
                    continue
                username = message[1]
                password = message[2]
                if authenticate(username, password):
                    active_users[cw] = {
                        "username": username,
                        "password": password
                    }
                else:
                    cw.write(b"Invalid password\n")
                    continue
                await broadcast(f"{username} joined the chat room\n", cw, False)
            elif command == ServerCommand.SEND:
                if cw not in active_users:
                    cw.write(b"You have to REGISTER. do REGISTER username\n")
                    continue
                if len(message) < 2:
                    cw.write("Type your message after SEND. try SEND I love you\n")
                    continue
                msg = " ".join(message[1:])
                await broadcast(f"{active_users[cw]['username']}: {msg}\n", cw)
            else:
                cw.write(f"Unknown command {command}\n".encode())
                write_help(cw)
    except asyncio.CancelledError:
        pass
    finally:
        cw.close()
        await cw.wait_closed()

async def main():
    server = await asyncio.start_server(client_connected_cb, host=HOST, port=PORT)
    
    addr = server.sockets[0].getsockname()
    print(f"[*] Server serving on {addr}")
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Closing server")
        exit(0)
