import socket
import threading
import struct
import json
import time
import os
import random
import math
from constnums import SKILLS,P_SPEED,GRAVITY,JUMP_CD,JUMP_SPEED,MAX_JUMP_COUNT

last_time=time.time()


class GameServer(threading.Thread):
    def __init__(self,name,password,host="0.0.0.0",port=5555):
        super().__init__(daemon=True)
        self.name=name
        self.password=password

        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind((host,port))
        self.sock.listen()


        self.players={}
        self.clients={}
        self.projectile=[]
        self.running=True
        self.gamestate="lobby"

        self.maps=[
                    "assets/map/map1.json",
                    "assets/map/map2.json"
                ]
        self.now_map=None
        self.map_data=None
        print("server created!")
    def run(self):

        print("listening...")

        while self.running:
            conn,addr=self.sock.accept()
            if len(self.clients)>=2:
                conn.sendall(b"ROOM_FULL")
                conn.close()
                continue

            print("client connected",addr)
            player_id=len(self.clients)+1
            self.clients[conn]={
                "id":player_id,
                "inputs":{},
                "skills":[1,2,3],
                "ready":False
            }
            self.players[conn]={
                "x":0,
                "y":300,
                "vx":P_SPEED,
                "vy":0,
                "ax":0,
                "ay":0,
                "pw":32,
                "ph":32,
                "dx":0,
                "dy":0,
                "jump_cd":0,
                "double_jump":0,
                "on_ground":False,
                "id":player_id,
                "skills":[1,2,3],
                "skill_cd":[0,0,0],
                "skill_count":[0,0,0],
                "skill_timer":[0,0,0],
            }

            
            self.send_packet(conn,{
                "type":"assign_id",
                "id":player_id
            })

            self.send_packet(conn,{"type":"current_players",
                                   "data":[{"player_id":p["id"],"skills":p["skills"],"ready":p["ready"] }
                                           for c,p in self.clients.items() if c!=conn]})

            self.broadcast({
                "type":"player_join",
                "data":{
                    "player_id":player_id
                }
            },sender=conn)

            threading.Thread(
                target=self.handle_client,
                args=(conn,),
                daemon=True
            ).start()

    def handle_client(self,conn):
        while True:
            try:
                raw_len=conn.recv(4)
                if not raw_len:
                    break
                msg_len=struct.unpack(">I",raw_len)[0]
                data=self.receive_fixed(conn,msg_len)
                if not data:
                    break
                msg=json.loads(data.decode())
                print("received",msg)
                self.handle_msg(conn,msg)

                #self.broadcast(msg,sender=conn)
            except Exception as e:
                print("server error",e)
                break
        print("client disconnected")
        del self.clients[conn]
        if self.gamestate=="lobby":
            del self.players[conn]
        conn.close()
    def receive_fixed(self,conn,length):
        data=b""
        while len(data)<length:
            chunk=conn.recv(length-len(data))
            if not chunk:
                return None
            data+=chunk
        return data

    def broadcast(self,msg_dict,sender=None):
        for conn in self.clients:
            if conn!=sender:
                self.send_packet(conn,msg_dict)

    def send_packet(self,conn,msg_dict):
        data=json.dumps(msg_dict).encode()
        packet=struct.pack(">I",len(data))+data
        conn.sendall(packet)


    def handle_msg(self,conn,msg):
        msg_type=msg["type"]
        data=msg.get("data",{})
        if msg_type=="inputs":
            self.clients[conn]["inputs"]=msg["data"]
        elif msg_type=="select_skill":
            self.handle_select(conn,data)
        elif msg_type=="ready":
            if self.gamestate=="lobby":
                self.handle_ready(conn,data)

    def handle_select(self,conn,data):
        player=self.clients.get(conn)
        if not player:
            return 
        skill_id=data["skill_id"]
        slot=data.get("slot",1)-1
        if 0<=slot<len(player["skills"]):
            
            player["skills"][slot]=skill_id

            print(f"player {player['id']} select skill {skill_id} in slot {slot}")

            self.broadcast({
                "type":"player_update",
                "data":{
                    "player_id":player["id"],
                    "skills":player["skills"]
                }
            })

    def handle_ready(self,conn,data):
        value=data.get("value",False)
        self.clients[conn]["ready"]=value

        player_id=self.clients[conn]["id"]

        self.broadcast({"type":"player_update",
                        "data":{
                            "player_id":player_id,
                            "ready":value
                        }
                    })
        
        if len(self.clients)==2 and all(p["ready"] for p in self.clients.values()):#測試用
            print("starting game")
            self.start_game()
            self.broadcast({"type":"gamestart"})
            self.gamestate="in game"
            
            threading.Thread(
                target=self.game_loop,
                daemon=True
            ).start()

    def start_game(self):
        for conn in self.clients:
            self.players[conn]["skills"]=self.clients[conn]["skills"]
            if self.players[conn]["id"]==1:
                self.players[conn]["x"]=100
            else:
                self.players[conn]["x"]=860
        self.choose_map()
    def choose_map(self):
        self.now_map=random.choice(self.maps)

        with open(self.now_map,"r",encoding="utf-8") as f:
            self.map_data=json.load(f)
        print(f"map {self.now_map}")
        self.broadcast({
            "type":"load_map",
            "data":{
                "map":os.path.basename(self.now_map)
            }
        })
        self.build_collision_grid()
    
    def build_collision_grid(self):
        collision_layer=next(
            l for l in self.map_data["layers"] 
            if l["name"]=="collision"
        )

        grid=collision_layer["data"]
        self.map_w=collision_layer["width"]
        self.map_h=collision_layer["height"]
        self.tile_size=self.map_data["tilewidth"]

        self.tile_grid=[]

        for y in range(self.map_h):
            row=[]
            for x in range(self.map_w):
                index=y * self.map_w + x
                row.append(grid[index]!=0)
            self.tile_grid.append(row)

        visited=[[False]*self.map_w for _ in range(self.map_h)]
        self.solid_rects=[]

        for y in range(self.map_h):
            for x in range(self.map_w):
                if not self.tile_grid[y][x] or visited[y][x]:
                    continue
                
                width=0
                while(x+width<self.map_w and
                      self.tile_grid[y][x+width] and
                        not visited[y][x+width]):
                    width+=1
                height=1
                done=False
                while y+height<self.map_h and not done:
                    for i in range(width):
                        if (not self.tile_grid[y+height][x+i] or
                            visited[y+height][x+i]):
                            done=True
                            break
                    if not done:
                        height+=1
                
                for dy in range(height):
                    for dx in range(width):
                        visited[y+dy][x+dx]=True

                world_x=x*self.tile_size-32
                world_y=y*self.tile_size-32

                self.solid_rects.append({
                    "x":world_x,
                    "y":world_y,
                    "w":width*self.tile_size,
                    "h":height*self.tile_size
                })
    def game_loop(self):
        TICK_RATE=60
        TICK_DT=1.0/TICK_RATE
        last=time.perf_counter()
        while self.running:
            now=time.perf_counter()
            dt=now-last

            if dt>=TICK_DT:
                last=now
                self.world_update(dt)
            else:
                time.sleep(0.001)

    def world_update(self,dt):
        for proj in self.projectile:
            proj["vx"]+=proj["ax"]*dt
            proj["vy"]+=proj["ay"]*dt

            proj["x"]+=proj["vx"]*dt
            proj["y"]+=proj["vy"]*dt

        for conn,p in self.players.items():
            inp=self.clients[conn].get("inputs",{})
            self.clients[conn]["inputs"]={}

            
            mx=inp.get("mx",0)
            my=inp.get("my",0)
            
            dir_x=inp.get("dir_x",0)
            jump=inp.get("jump",False)
            skill_key=inp.get("skill_key",None)
            #x軸移動
            p["vx"]+=p["ax"]*dt
            new_x=p["x"]+dir_x*p['vx']*dt
            
            player_rect={
                "x":new_x,
                "y":p["y"],
                "w":p["pw"],
                "h":p["ph"]
            }
            
            for rect in self.solid_rects:
                if self.rect_collide(player_rect,rect):
                    if dir_x>0:
                        new_x=rect["x"]-p["pw"]
                    elif dir_x<0:
                        new_x=rect["x"]+rect["w"]
                    break
            p["x"]=new_x
            #y軸移動

            if p["jump_cd"]>0:
                p["jump_cd"]-=dt
                if p['jump_cd']<0:
                    p["jump_cd"]=0
            if jump :
                if p["on_ground"]:
                    p["vy"]=JUMP_SPEED
                    p["double_jump"]=1           
                    p["on_ground"]=False
                    p["jump_cd"]=0
                elif p['double_jump']<MAX_JUMP_COUNT and p["jump_cd"]==0:
                    p["vy"]=JUMP_SPEED
                    p["double_jump"]+=1
                    p["jump_cd"]=JUMP_CD

            p["vy"]+=GRAVITY*dt
            new_y=p["y"]+p['vy']*dt

            player_rect["x"]=new_x
            player_rect["y"]=new_y

            for rect in self.solid_rects:
                if self.rect_collide(player_rect,rect):
                    if p["vy"]>0:
                        p["on_ground"]=True
                        p["double_jump"]=0
                        new_y=rect["y"]-p["ph"]
                    elif p["vy"]<0:
                        new_y=rect["y"]+rect["h"]
                    p["vy"]=0
                    break
            
            p['y']=new_y



            #skill
            dx=mx-p["x"]-16
            dy=my-p["y"]-16
            p["dx"]=dx
            p["dy"]=dy
            D=math.hypot(dx,dy)
            if D>0:
                wx=dx/D
                wy=dy/D
            else:
                wx,wy=1,0

            for i in range(3):
                if p["skill_cd"][i]>0:
                    p["skill_cd"][i]-=dt
                    if p["skill_cd"][i]<0:
                        p["skill_cd"][i]=0

            for i in range(3):
                if p["skill_timer"][i]>0:
                    p["skill_timer"][i]-=dt
                    if p["skill_timer"][i]<0:
                        p["skill_timer"][i]=0
            
            
            
            if skill_key is not None:
                slot=skill_key-1
                if not p["skill_cd"][slot]:
                    skill_using=SKILLS[p["skills"][slot]-1]
                    p["skill_cd"][slot]=skill_using["cd"]
                    if skill_using["type"]=="projectile":
                        p["skill_count"][slot]=skill_using["amount"]

            for i in range(3):
                if p["skill_count"][i] and p["skill_timer"][i]==0:
                    skill_using=SKILLS[p["skills"][i]-1]
                    p["skill_count"][i]-=1
                    p["skill_timer"][i]=skill_using["atkspeed"]
                    if skill_using["type"]=="projectile":
                        self.spawn_projectile(p,skill_using,wx,wy,p["skills"][i])


        self.broadcast_world_state()

    def spawn_projectile(self,p,skill,wx,wy,skill_id):
        
        a=skill.get("a",0)
        proj={
            "x":p["x"],
            "y":p["y"],
            "vx":skill["speed"]*wx,
            "vy":skill["speed"]*wy,
            "ax":a*wx,
            "ay":a*wy,
            "dmg":skill["dmg"],
            "owner":p["id"],
            "skill_id":skill_id
        }
        self.projectile.append(proj)

    def rect_collide(self,r1,r2):
        return(
            r1["x"]<r2["x"]+r2["w"] and
            r1["x"]+r1["w"]>r2["x"] and
            r1["y"]<r2["y"]+r2["h"] and
            r1["y"]+r1["h"]>r2["y"]
        )



    def broadcast_world_state(self):
        snapshot_player=[]
        snapshot_proj=[]
        for p in self.players.values():
            snapshot_player.append({
                "player_id":p["id"],
                "x":p["x"],
                "y":p["y"],
                "dx":p["dx"],
                "dy":p["dy"],
                "skill_cd":p["skill_cd"]
            })
        for proj in self.projectile:
            snapshot_proj.append({
                "x":proj["x"],
                "y":proj["y"],
                "owner":proj["owner"],
                "skill_id":proj["skill_id"]
            })
        self.broadcast({
            "type":"world_state",
            "data":{
                "players":snapshot_player,
                "proj":snapshot_proj
            }
        })