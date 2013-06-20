import cocos
from cocos import menu
from cocos.scene import Scene
from cocos.director import director
import pyglet
import socket
import collections
import string
import re
import logging

FONT = "Consolas"


check_time = 0.1
check_conn_time = 1

class Input(cocos.cocosnode.CocosNode):

    def on_enter(self):
        document = pyglet.text.document.FormattedDocument()
        self.layout = pyglet.text.layout.IncrementalTextLayout(document, 70, 70)
        self.layout.x = 100
        self.layout.y = 100
        caret = pyglet.text.caret.Caret(self.layout)

    def draw(self):
        self.layout.draw()


class EventLayer(cocos.layer.Layer):
    is_event_handler = True
    
    VALID_CHARS = string.ascii_uppercase
    CHATPOS = (100,120)
    
    
    def __init__(self, lobby):
        super(EventLayer,self).__init__()
        self.lobby = lobby
        print "HELLO ENTER"
        self.chat_msg = ""
        self.chat_label = cocos.text.Label(self.chat_msg, self.CHATPOS,font_name=FONT)
        self.add(self.chat_label)
        self.chat_active = True

    def on_enter(self):
        #batch = pyglet.graphics.Batch()
        #document = pyglet.text.document.FormattedDocument()
        #layout = pyglet.text.layout.IncrementalTextLayout(document, 70, 70)
        #layout.x = 100
        #layout.y = 100
        #self.caret = pyglet.text.caret.Caret(layout)
        #director.window.push_handlers(self.caret)
        pass

    def on_exit(self):
        #director.window.remove_handlers(self.caret)
        pass
    
    def on_key_press(self,key,modifiers):
        skey = pyglet.window.key.symbol_string(key)
        print "Skey: ", skey
        modifiers = pyglet.window.key.modifiers_string(modifiers).split("|")
        if self.chat_active:
            if skey == "BACKSPACE":
                if "MOD_CTRL" in modifiers:
                    chat = self.chat_msg [::-1]
                    r = re.search("\s+",chat)
                    if r:
                        self.chat_msg = chat[:r.span()[0]:-1]
                    else:
                        pass
                else:
                    self.chat_msg = self.chat_msg[:-1]
            if skey == "RETURN":
                self.parent.send_chat(self.chat_msg)
                self.chat_msg = ""
            self.update_chat()
        if skey == "RETURN":
            self.lobby.start_game(None,None) #FIXME
            
    def on_text(self,text):
        print "text: ", text
        if self.chat_active:
            self.chat_msg += text
            self.update_chat()

    def on_text_motion(self, motion):
        print "motion: "
        logging.info(motion)
                
    def on_key_release(self, key, modifiers):
        print "key release: ", key
        
    def update_chat(self):
        print "chat is: ",self.chat_msg
        self.chat_label.kill()
        self.chat_label = cocos.text.Label(self.chat_msg, self.CHATPOS,font_name=FONT,font_size=14)
        self.add(self.chat_label)
        
class Gui(cocos.layer.Layer):
    USERPOS = (600,500)
    STARTBUTTON = (600,100)

    def __init__(self, host):
        super(Gui,self).__init__()
        
        self.host = host
        self.chat = collections.deque([],10)
        self.labels = []
        self.users = []
        self.users_labels = []
        self.menu = self.Menu(self.host)
        self.add(self.menu)

    
    def get_users(self):
        return self.users
    
    def add_user(self,name):
        self.users.append(name)
        self._update_users()
        
    def remove_user(self,name):
        self.users.remove(name)
        self._update_users()
        
    def _update_users(self):
        for l in self.users_labels:
            l.kill()
            
        self.users_labels = []
        
        for i,u in enumerate(self.users):
            x,y = self.USERPOS
            if i == 0:
                u = u+"(me)"
            l = (cocos.text.Label(u,(x,y-i*20),font_name=FONT,font_size=14))
            self.users_labels.append(l)
            self.add(l)
        
    def add_chat(self,line):
        for l in self.labels:
            l.kill()
            
        self.labels = []
            
        self.chat.appendleft(line)
        for n,i in enumerate(self.chat):
            label = cocos.text.Label(i,(100,150+n*20),font_name=FONT,font_size=14)
            self.labels.append(label)
            self.add(label)

    class Menu(cocos.menu.Menu):
        colours = [(255, 100, 220), (129, 255, 100), (50, 50, 100), 
                    (100, 180, 255), (220, 130, 190), (130, 240, 180), 
                    (230, 134, 184), (255, 200, 150)]
        def __init__(self, host):
            super(Gui.Menu, self).__init__("")
            items = []
            positions = []
            if host:
                items.append((cocos.menu.MenuItem('Start Game', self.on_start)))
                positions.append((200, 70))
            else:
                items.append((cocos.menu.ToggleMenuItem('Ready: ', self.set_ready)))
                positions.append((200, 70))
            items.extend(
                [cocos.menu.ColorMenuItem("Colour", self.on_colour, self.colours)]
                )
            positions.extend([(130,400)])
            self.create_menu(items, selected_effect=cocos.menu.shake(),
                              unselected_effect=cocos.menu.shake_back(),
                              layout_strategy=cocos.menu.fixedPositionMenuLayout(
                                positions))
        def on_quit( self ):
            exit()

        def on_start(self):
            print "Hello?"
            self.parent.parent.start_game()

        def on_colour(self, idx):
            pass

        def set_ready(self, b):
            pass
            
class LobbyScene(Scene):
    
    def __init__(self,port,name):
        
        super(LobbyScene,self).__init__()
        
        self.name = name
        self.gui = Gui(host=True)
        self.gui.add_user(name)    
        self.add(self.gui)
        self.event_layer = EventLayer(self)
        self.add(self.event_layer)
        self.schedule_interval(self.check_msg, check_time)
        self.connections = []
        self.chat = []
        #self.input = Input()
        #self.add(self.input)
        
        self.ip = socket.gethostbyname(socket.gethostname())
        self.add(cocos.text.Label("Local ip: "+str(self.ip),(100,550)))
        
        server = socket.socket()
        server.bind(("",port))
        server.listen(10)
        server.setblocking(0)
        #server.setblocking(0)
        
        self.server = server
        self.schedule_interval(self.check_connection,check_conn_time)
                
    def check_connection(self,dt):
        try:
            conn,addr = self.server.accept()
            print "got connection, waiting for answer!" 
            name = conn.recv(12).rstrip(" ")
            conn.send(self.name.ljust(12))
            self.send("USER JOINED:"+name)
            print "name is: ", name
            self.connections.append((conn,addr,name))
            conn.send(("USERS: "+",".join(self.gui.get_users())).ljust(128))
            self.gui.add_user(name)
            self.gui.add_chat(name + " has joined the game")
            
            
        except socket.error as e:
            if e.errno == 10035:
                pass
            else:
                raise
            
            
        
    def check_msg(self,dt):
        for conn,addr,name in self.connections:
            try:
                msg = conn.recv(1024)
                if msg:
                    print repr(msg)+"|"+repr(addr)+"|"+repr(name)
                    if msg.startswith("CHAT: "):
                        print "Incoming chat"
                        self.send_chat(msg[6:],name)
                        print msg
                        
            except socket.error as e:
                if e.errno == 10035:
                    pass
                elif e.errno == 10054: #Left the game
                    self.gui.add_chat(name + " has left the game")
                    conn.close()
                    self.connections.remove((conn,addr,name))
                    self.send("USER LEFT:"+name)
                    self.gui.remove_user(name)
                else:
                    raise
                
    def send_chat(self,msg,sender=None):
        if not sender:
            sender = self.name
        self.gui.add_chat(sender + ": "+msg)
        for conn,addr,name in self.connections:
            conn.send("CHAT: "+sender+":"+msg)
        
    def send(self,message):
        for conn,addr,name in self.connections:
            conn.send(message)
            
    def start_game(self):
        tile_map = None
        game_map = None
        for conn, addr, name in self.connections:
            conn.send("START")
            
        import game
        print "Starting a game scene with: ", tile_map, game_map, self.connections, True
        director.replace(game.GameScene(tile_map, game_map, clients = self.connections, host=True))
        
            
                    
class JoinLobby(Scene):
    def __init__(self,ip,port,name):
        super(JoinLobby,self).__init__()
        
        self.gui = Gui(host=False)
        self.add(self.gui)
        self.gui.add_user(name)
        
        self.event_layer = EventLayer(self)
        self.add(self.event_layer)

        conn = socket.socket()
        conn.connect((ip,port))
        conn.send(name.ljust(12))
        self.hoster_name = conn.recv(12)
        users = conn.recv(128)[7:].rstrip()
        print "users: ",repr(users)
        for u in users.split(","):
            self.gui.add_user(u)
        conn.setblocking(0)
        self.conn = conn
        self.schedule_interval(self.check_msg, check_time)
        
        self.gui.add_chat("You have joined the game")
        
        
    def check_msg(self,dt):
        try:    
            msg = self.conn.recv(1024)
            print "Recieved from server: ",repr(msg)
            if msg:
                if msg.startswith("CHAT: "):
                    self.gui.add_chat(msg[6:]+"  ")
                elif msg.startswith("USER"):
                    if msg.startswith("USER LEFT:"):
                        user = msg.split(":")[1]
                        self.gui.remove_user(user)
                        self.gui.add_chat(user+" has left the game")
                    elif msg.startswith("USER JOINED:"):
                        user = msg.split(":")[1]
                        self.gui.add_user(user)
                        self.gui.add_chat(user+" has joined the game")
                elif msg.startswith("START"):
                    self.start_game()
                    
                    
                    
                    
        except socket.error as e:
            if e.errno == 10035:
                pass
            else:
                raise
            
    def send_chat(self,msg):
        self.conn.send("CHAT: "+msg)
        
    def start_game(self):
        import game
        director.replace(scene = game.GameScene(None,None,clients=self.conn, host=False))
        

class JoinMenu(menu.Menu):
    def __init__(self):
        super( JoinMenu, self ).__init__("Join a game!" )

        self.menu_valign = menu.CENTER
        self.menu_halign = menu.CENTER
        self.port = 8035
        self.ip = "127.0.0.1"
        self.nickname = "Badlybader"

        # then add the items
        items = [
            (menu.EntryMenuItem('Nickname:', self.on_name_change, "default_name", max_length=14) ),
            (menu.EntryMenuItem('IP-address:', self.on_ip_change, '127.0.0.1', max_length=15)),
            (menu.EntryMenuItem('Port:', self.on_port_change, '8035', max_length=15)),
            (menu.MenuItem('Join game', self.join))
        ]
        
        self.create_menu( items, menu.shake(), menu.shake_back() )
        
    def on_name_change(self, value):
        self.nickname = value
        
    def on_ip_change(self,value):
        self.ip = value
        
    def on_port_change(self,value):
        self.port = int(value)
        
    def join(self):
        director.push(JoinLobby(self.ip,self.port,self.nickname))
        
    def on_quit( self ):
        self.parent.switch_to( 0 )
        


class HostMenu(menu.Menu):
    def __init__(self):
        super( HostMenu, self ).__init__("Host a game!" )

        self.menu_valign = menu.CENTER
        self.menu_halign = menu.CENTER
        self.port = 8035
        self.ip = socket.gethostbyname(socket.gethostname())
        self.nickname = "Badlybader"

        player_name = OPTIONS.get("player_name") or "Player" #Example of how passing options should be used


        # then add the items
        items = [
            (menu.EntryMenuItem('Nickname:', self.on_name_change, player_name, max_length=14)),
            (menu.EntryMenuItem('Port:', self.on_port_change, '8035',max_length=5)),
            (menu.MenuItem('Host game!', self.host)) 
            ]
        
        self.create_menu( items, menu.shake(), menu.shake_back() )
    def on_name_change(self, value):
        self.nickname = value
    
    def on_port_change(self,port):
        self.port = int(port)
        self.parent.ip_label = "Your local ip: %s:%s"%(self.ip,self.port)
    
    def host(self): #NYI
        director.push(LobbyScene(self.port,self.nickname))
    
    def on_quit( self ):
        self.parent.switch_to( 0 )
        
        
class Menu(menu.Menu):
    def __init__(self):
        print "ELLO"
        super( Menu, self ).__init__("Multiplayer!" )

        self.menu_valign = menu.CENTER
        self.menu_halign = menu.CENTER

        # then add the items
        items = [
            ( menu.MenuItem('Host server', self.host ) ),
            ( menu.MenuItem('Join game', self.join ) )
        ]
        
        self.create_menu( items, menu.shake(), menu.shake_back() )
        
    def host(self):
        self.parent.switch_to(1)
    
    def join(self):
        self.parent.switch_to(2)
        
    def on_quit(self):
        director.pop()
        
#ip = socket.gethostbyname(socket.gethostname())
#port = 8035
#ip_label = cocos.text.Label("Your local ip: %s:%s"%(ip,port),(200,300))

def CreateScene(layer=None, **opts):
    """Creates the menu for hosting/joining a game.
        Layer will be added as a layer to the final lobby layer so you can catch user input etc.

        Once the game starts, connection info and the layer passed, if given, will be returned"""
    global OPTIONS
    OPTIONS = opts
    scene = cocos.scene.Scene(cocos.layer.MultiplexLayer(Menu(),HostMenu() ,JoinMenu()))
    return
