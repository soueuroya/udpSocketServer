### Daniel Boldrin
# 101143582

import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()  # We'll use this to keep our clients list safe later.

clients = {} # A list of clients currently connected. Obviously, there's no one here yet, so it's empty. 

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024) # Receive data from the socket and put it into a tuple. Data is the actual data being sent, and addr is the address the data came from
      # 'address' refers to the IP and port they're using. 
      dataStr = str(data) # Turn the data part into a string.
      AlreadyHerePlayerList = {"cmd": 3, "players": []} # A list of players that are already online when a new client joins.
      if addr in clients: # If the address the data came from is already in our list of clients...
         if 'heartbeat' in dataStr: # and if we find the word 'heartbeat' in what they sent
            # If the server receives a heartbeat message, it updates the corresponding client with the last heartbeat time. 
            clients[addr]['lastBeat'] = datetime.now()
         else: # The only other thing this could be right now is a position update about the client we got the message from, so just assume it is that. 
         # This is dangerous and not optimal, but it does work.
         # This is how the server knows a client has moved.
            dataJson = json.loads(data) # Turn the data we got into a json file.
            # Parse the json file we just made and put the info into the 'position' field of the client who has the address we got the message from.
            clients[addr]['position'] = {"x": dataJson['position']['x'], "y": dataJson['position']['y'], "z": dataJson['position']['z']} 
            
            
      else:
         if 'connect' in dataStr: # the server expects a packet with "connect" in order for a client to connect
            # When a new client connects, the server adds the new client to a list of clients it has.
            clients[addr] = {} # Make a new entry in our clients lst
            clients[addr]['lastBeat'] = datetime.now() # Treat this connect message as the last heartbeat and set it to now.
            clients[addr]['position'] = 0 # Zero out the position we currently have for the client.
            message = {"cmd": 0,"player":{"id":str(addr)}} # Make a message! It's a dictionary that holds another dictionary. A nested dictionary. A Matryoshka dictionary.
            # Its key is cmd 0, which means it's a connect message, and it will hold a dictionary called player.
            # The dictionary called player holds an address called 'id'. 
            m = json.dumps(message) # Store the message we made in a json.
            
            for c in clients:
               sock.sendto(bytes(m,'utf8'), (c[0],c[1])) # When a new client connects, send a message to all currently connected clients.
               # This is like announcing that someone has arrived at a party.
               player = {} # Make an empty dictionary called player.
               player['id'] = str(c) # Set the id of the player to the address of the client
               AlreadyHerePlayerList['players'].append(player) # Add the player who just joined to the list of players who are already at the party.

            ncm = json.dumps(AlreadyHerePlayerList) # Put that list into a json
            sock.sendto(bytes(ncm,'utf8'), (addr[0],addr[1])) # Send id of each client TO NEW CLIENT 



def cleanClients(sock):
   while True:
      for c in list(clients.keys()): # Iterate through all the clients using their IPs
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5: # If we haven't heard a heartbeat in over 5 seconds
            #print('Dropped Client: ', c)
            # Threading is confusing. If you don't get it, go here before you read the next part. http://effbot.org/zone/thread-synchronization.htm
            clients_lock.acquire() # We don't want more than one thread messing with the client list, so lock it for now.
            del clients[c] # Delete the client at this address
            clients_lock.release() # Release the lock
            # If a client is dropped, the server sends a message to all clients currently connected 
            # to inform them of the dropped player. 
            for cc in clients: # The client has been dropped, now iterate through all connected clients
               droppedClientMsg = {"cmd": 2, "id":str(c)} # Get the id of the client that dropped 
               dcp = json.dumps(droppedClientMsg) # Store in json
               sock.sendto(bytes(dcp,'utf8'), (cc[0],cc[1])) # Send json to each client
               #print('Sent message to current client informing of dropped client')
      time.sleep(1)

def gameLoop(sock): 
   while True:
      GameState = {"cmd": 1, "players": []} # Make a dictionary that holds the cmd (command) 1 (as far as the client is concerned, this means it's a simple update)
      # and an (empty currently) array of players
      clients_lock.acquire() # We don't want more than one thread messing with the client list, so lock it for now.
      #print (clients)
      for c in clients: # Go through our list of clients
         player = {} # Make a new player dictionary
         player['id'] = str(c) # Set the id of the new player
         player['position'] = clients[c]['position'] # Set the position to the position we received from the client.
         GameState['players'].append(player) # Add the player to our list of players
      s=json.dumps(GameState) # Put that list of players in a json
      #print(s)
      for c in clients: #go through our list of clients again
         sock.sendto(bytes(s,'utf8'), (c[0],c[1])) #Send that message - s - to every client
      clients_lock.release() # Release the lock
      time.sleep(.03) # Wait for a thirtieth of a second before doing this again

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Creates a new socket of type UDP (user datagram protocol, the fast but unreliable one) (DGRAM, or datagram). 
   # A datagram socket is the sending or receiving point for a packet delivery service.
   s.bind(('', port)) # Binds the newly created socket to local IP ('') and port (12345)
   start_new_thread(gameLoop, (s,)) # Start a new thread and send the socket we just made to it. Repeat x2.
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1) # Go to sleep. This keeps the main thread going - if the main thread exits, every other thread you start will stop!

if __name__ == '__main__': # If we're running this as the source file (we are), run main. This safeguards the code parts which are not to be executed when invoked from other files.
   main()
