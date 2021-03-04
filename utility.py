# xysun's code was used as template
import socket, pdb

MAX_CLIENTS = 20
PORT = 2233
QUIT_STRING = '<$quit$>'


def create_socket(address):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind(address)
    s.listen(MAX_CLIENTS)
    print("Now listening at ", address)
    return s

class Hall:
    def __init__(self):
        self.rooms = {} # {room_name: Room}
        self.room_player_map = {} # {playerName: roomName}

    def welcome_new(self, new_player):
        new_player.socket.sendall(b'\nPlease tell us your name:\n')

    def list_rooms(self, player):
        
        if len(self.rooms) == 0:
            msg = 'No rooms created\n' \
                + 'Use <-join- room_name> to create a room.\n'
            player.socket.sendall(msg.encode())
        else:
            msg = 'Available rooms\n'
            for room in self.rooms:
                msg += room + ": " + str(len(self.rooms[room].players)) + " users\n"
            player.socket.sendall(msg.encode())
    
    def handle_msg(self, player, msg):
        
        instructions = b'Instructions:\n'\
            + b'<-list-> to show all rooms\n'\
            + b'<-join->room_name] to join to a room\n' \
            + b'<-manual-> to show instructions\n' \
            + b'<-quit-> to exit room\n' \
            + b'\n'

        print(player.name + " says: " + msg)
        if "name:" in msg:
            name = msg.split()[1]
            player.name = name
            print("New connection from:", player.name)
            player.socket.sendall(instructions)

        elif "-join-" in msg:
            same_room = False
            if len(msg.split()) >= 2: # check if too many arguments
                room_name = msg.split()[1]
                if player.name in self.room_player_map: # switching to same room?
                    if self.room_player_map[player.name] == room_name:
                        player.socket.sendall(b'You are already in room: ' + room_name.encode())
                        same_room = True
                    else: # switch
                        old_room = self.room_player_map[player.name]
                        self.rooms[old_room].remove_player(player)
                if not same_room:
                    if not room_name in self.rooms: # new room:
                        new_room = Room(room_name)
                        self.rooms[room_name] = new_room
                    self.rooms[room_name].players.append(player)
                    self.rooms[room_name].welcome_new(player)
                    self.room_player_map[player.name] = room_name
            else:
                player.socket.sendall(instructions)

        elif "-list-" in msg:
            self.list_rooms(player) 

        elif "-manual-" in msg:
            player.socket.sendall(instructions)
        
        elif "-quit-" in msg:
            player.socket.sendall(QUIT_STRING.encode())
            self.remove_player(player)

        else:
            # check if in a room
            if player.name in self.room_player_map:
                self.rooms[self.room_player_map[player.name]].broadcast(player, msg.encode())
            else:
                msg = 'You are currently not in any room! \n' \
                    + 'Use [<list>] to see available rooms! \n' \
                    + 'Use [<join> room_name] to join a room! \n'
                player.socket.sendall(msg.encode())
    
    def remove_player(self, player):
        if player.name in self.room_player_map:
            self.rooms[self.room_player_map[player.name]].remove_player(player)
            del self.room_player_map[player.name]
        print("Player: " + player.name + " has left\n")

    
class Room:
    def __init__(self, name):
        self.players = [] # socket list
        self.name = name

    def welcome_new(self, from_player):
        msg = self.name + " welcomes: " + from_player.name + '\n'
        for player in self.players:
            player.socket.sendall(msg.encode())
    
    def broadcast(self, from_player, msg):
        msg = from_player.name.encode() + b":" + msg
        for player in self.players:
            player.socket.sendall(msg)

    def remove_player(self, player): # leaving room
        self.players.remove(player)
        leave_msg = player.name.encode() + b"has left the room\n"
        self.broadcast(player, leave_msg)

class Player:
    def __init__(self, socket, name = "new"):
        socket.setblocking(0)
        self.socket = socket
        self.name = name

    def fileno(self):
        return self.socket.fileno()
