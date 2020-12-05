import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}
def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      dataString = str(data)
      
      #Send a list of the players connected
      PlayersInGameList = {"cmd": 3, "players": []} 
      if addr in clients:
         if 'heartbeat' in dataString:
            clients[addr]['lastBeat'] = datetime.now()
         else:#hope this works.
            otherData = json.loads(data)#get the data then store it below in client dict.
            clients[addr]['position'] = otherData['position']

      else:
         if 'connect' in dataString:
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            #add position to this dictionary
            clients[addr]['position'] = 0
            #get this connected players id
            message = {"cmd": 0,"player":{"id":str(addr)}}
            m = json.dumps(message)
            for c in clients:
               #send the players id to all players in clients.
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
             
               #we need to set the players id in the player dict
               player = {}#set the new player list
               player['id'] = str(c)#
               #and also append this new player to the list of existing players
               PlayersInGameList['players'].append(player)

            #while running through addr in clients, (line 19)
            #Create a json dump of our made list of players in the game above
            #and send it to everyone in clients.
            sock.sendto(bytes(json.dumps(PlayersInGameList), 'utf8'), (addr[0],addr[1]))


def cleanClients(sock):
   while True:
      #a little more straight forward, loop through all the clients,
      #check for a disconnect, while in that loop, if a disconnection occurs,
      #loop through all clients and notify them.
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
             
           
            for cl in list(clients.keys()):
               dmessage = {"cmd": 2, "id":str(c)}
               m = json.dumps(dmessage)
               sock.sendto(bytes(m,'utf8'), (cl[0],cl[1]))
            clients_lock.acquire() 
            del clients[c]
            clients_lock.release()   
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      #print (clients) remove this because its annoying and why would u need
      #all this data every couple of seconds......
      for c in clients:
         player = {}
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         #leave color in, might as well. 
         #but add position by copying the player position to client position
         #because convoluted = good?
         player['position'] = clients[c]['position']
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      #print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()

      
      time.sleep(.03)

def main():
   port = 12345
  
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)
      


if __name__ == '__main__':
   main()
