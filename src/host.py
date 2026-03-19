import socket
import threading
import struct
import json
import time
import os
import random
import math
from constnums import SKILLS,P_SPEED,GRAVITY,JUMP_CD,JUMP_SPEED,MAX_JUMP_COUNT,PLAYER_BSAE_SIZE

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

        self.next_projectile_id=0
        print("server created!")
    def run(self):
        try:
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
                    "hp":500,
                    "jump_cd":0,
                    "double_jump":0,
                    "on_ground":False,
                    "id":player_id,
                    "conn":conn,
                    "skills":[1,2,3],
                    "skill_cd":[0,0,0],
                    "skill_count":[0,0,0],
                    "skill_timer":[0,0,0],
                    "alive":True,
                    "can_move":True,
                    "invincible":False,
                    "state":"normal",
                    "dashvx":0,
                    "dashvy":0,
                    "dash_hit":True,
                    "rect":None,
                    "scale":1,
                    "last_scale":1
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
        except Exception as e:
            print("server error",e)

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
        
        if len(self.clients)>=1 and all(p["ready"] for p in self.clients.values()):#測試用
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
            self.players[conn]["rect"]={"x":self.players[conn]["x"],
                                            "y":self.players[conn]["y"],
                                            "w":self.players[conn]["pw"],
                                            "h":self.players[conn]["ph"]
                                            }
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

    def proj_x_collide(self,proj):
        cx=proj["x"]
        cy=proj["y"]
        r=proj["r"]
        for rect in self.solid_rects:
            closest_x=max(rect["x"],min(cx,rect["x"]+rect["w"]))
            closest_y=max(rect["y"],min(cy,rect["y"]+rect["h"]))

            dx=cx-closest_x
            dy=cy-closest_y
            
            if proj["life"]:
                if dx*dx+dy*dy<r*r:
                    if proj["vx"]>0:
                        proj["x"]=rect["x"]-r
                    else:
                        proj["x"]=rect["x"]+rect["w"]+r
                    proj["life"]-=1
                    proj["vx"]*=-1
                    break
    def proj_y_collide(self,proj):
        cx=proj["x"]
        cy=proj["y"]
        r=proj["r"]
        for rect in self.solid_rects:
            closest_x=max(rect["x"],min(cx,rect["x"]+rect["w"]))
            closest_y=max(rect["y"],min(cy,rect["y"]+rect["h"]))

            dx=cx-closest_x
            dy=cy-closest_y
            
            if proj["life"]:
                if dx*dx+dy*dy<r*r:
                    if proj["vy"]>0:
                        proj["y"]=rect["y"]-r
                    else:
                        proj["y"]=rect["y"]+rect["h"]+r
                    proj["life"]-=1
                    proj["vy"]*=-1
                    break
    def circle_player_collide(self,circle,P):
        cx=circle["x"]
        cy=circle["y"]
        r=circle["r"]

        closest_x=max(P["x"],min(cx,P["x"]+P["pw"]))
        closest_y=max(P["y"],min(cy,P["y"]+P["ph"]))

        dx=cx-closest_x
        dy=cy-closest_y
        if dx*dx+dy*dy<r*r:
            return True
        
        return False
    def world_update(self,dt):
        for conn,p in self.players.items():
            old_x,old_y=p["x"],p["y"]
            if p["scale"]!=p["last_scale"]:
                center_x=p["x"]+p["pw"]/2
                center_y=p["y"]+p["ph"]/2
                p["pw"]=p["scale"]*PLAYER_BSAE_SIZE
                p["ph"]=p["scale"]*PLAYER_BSAE_SIZE
                p["x"]=center_x-p["pw"]/2
                p["y"]=center_y-p["ph"]/2
            
            player_rect={
                "x":p["x"],
                "y":p["y"],
                "w":p["pw"],
                "h":p["ph"]
            }


            for rect in self.solid_rects:
                if self.rect_collide(player_rect,rect):
                    dx_left=(rect["x"]-(p["x"]+p["pw"]))
                    dx_right=((rect["x"]+rect["w"])-p["x"])
                    dy_top=(rect["y"]-(p["y"]+p["ph"]))
                    dy_bottom=((rect["y"]+rect["h"])-p["y"])

                    min_fix=min(
                        abs(dx_left),abs(dx_right),
                        abs(dy_top),abs(dy_bottom)
                    )

                    if min_fix==abs(dx_left):
                        p["x"]+=dx_left
                    elif min_fix==abs(dx_right):
                        p["x"]+=dx_right
                    elif min_fix==abs(dy_top):
                        p["y"]+=dy_top
                    else:
                        p["y"]+=dy_bottom

                    player_rect["x"]=p["x"]
                    player_rect["y"]=p["y"]

            new_x=p["x"]
            if p["can_move"]:
                inp=self.clients[conn].get("inputs",{})
                self.clients[conn]["inputs"]={}
                mx=inp.get("mx",None)
                my=inp.get("my",None)
                
                dir_x=inp.get("dir_x",0)
                jump=inp.get("jump",False)
                skill_key=inp.get("skill_key",None)
                if not p["alive"]:
                    jump=False
                    dir_x=0
                    skill_key=None
                #x軸移動
                if p["state"]=="movement":
                    new_x=p["x"]+p["dashvx"]*dt
                elif p["state"]=="normal":
                    if dir_x!=0:
                        p["vx"]=P_SPEED
                    p["vx"]+=p["ax"]*dt
                    new_x=p["x"]+dir_x*p['vx']*dt/p["scale"]
                
            player_rect["x"]=new_x
            
            for rect in self.solid_rects:
                if self.rect_collide(player_rect,rect):
                    if p["state"]=="movement":
                        if p["dashvx"]>0:
                            new_x=rect["x"]-p["pw"]
                        elif p["dashvx"]<0:
                            new_x=rect["x"]+rect["w"]
                    else:
                        if dir_x>0:
                            new_x=rect["x"]-p["pw"]
                        elif dir_x<0:
                            new_x=rect["x"]+rect["w"]
                    break
            p["x"]=new_x
            player_rect["x"]=p["x"]

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
            if p["state"]=="normal":
                p["vy"]+=GRAVITY*dt
                new_y=p["y"]+p['vy']*dt/p["scale"]
            elif p["state"]=="movement":
                new_y=p["y"]+p["dashvy"]*dt

            player_rect["y"]=new_y

            for rect in self.solid_rects:
                if self.rect_collide(player_rect,rect):
                    if p["state"]=="movement":
                        if p["dashvy"]>0:
                            p["on_ground"]=True
                            p["double_jump"]=0
                            new_y=rect["y"]-p["ph"]
                        elif p["dashvy"]<0:
                            new_y=rect["y"]+rect["h"]
                    else:
                        if p["vy"]>0:
                            p["on_ground"]=True
                            p["double_jump"]=0
                            new_y=rect["y"]-p["ph"]
                        elif p["vy"]<0:
                            new_y=rect["y"]+rect["h"]
                    p["vy"]=0
                    break
            
            p['y']=new_y
            p["rect"]=player_rect
            p["last_scale"]=p["scale"]
            if p["state"]=="movement" and not p["dash_hit"]:
                for other in self.players.values():
                    if other["id"]==p["id"]:
                        continue
                    if self.rect_collide(p["rect"],other["rect"]):
                        if not other["invincible"] and other["alive"]:
                            other["hp"]-=SKILLS[2]["dmg"]*p["scale"]
                            p["dash_hit"]=True
                            if other["hp"]<=0:
                                    other["alive"]=False
                                    other["hp"]=0
                            break
            #skill
            if mx is None or my is None:
                dx=p['dx']
                dy=p['dy']
            else:
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
                    if skill_using["type"]=="movement":
                        p["skill_count"][slot]=skill_using.get("amount",1)
                    if skill_using["type"]=="sword":
                        p["skill_count"][slot]=skill_using.get("amount",1)
                    if skill_using["type"]=="transform":
                        p["skill_count"][slot]=skill_using.get("amount",2)
            if p["alive"]:
                for i in range(3):
                    if p["skill_count"][i] and p["skill_timer"][i]==0:
                        skill_using=SKILLS[p["skills"][i]-1]
                        p["skill_count"][i]-=1
                        p["skill_timer"][i]=skill_using["atkspeed"]
                        if skill_using["type"]=="projectile":
                            self.spawn_projectile(p,skill_using,wx,wy,p["skills"][i])
                        if skill_using["type"]=="movement":
                            self.use_movement_skill(skill_using,wx,wy,p["skill_count"][i],p)
                        if skill_using["type"]=="sword":
                            self.spawn_sowrd(skill_using,wx,wy,p,D)
                        if skill_using["type"]=="transform":
                            self.use_transform(skill_using,p["skill_count"][i],p)
            
        for proj in self.projectile:
            if not proj["life"]:
                continue
            proj["vx"]+=proj["ax"]*dt
            proj["vy"]+=proj["ay"]*dt

            proj["x"]+=proj["vx"]*dt
            self.proj_x_collide(proj)

            proj["y"]+=proj["vy"]*dt
            self.proj_y_collide(proj)
            for conn,player in self.players.items():
                if player["id"]!=proj["owner"]:
                    if self.circle_player_collide(proj,player):
                        proj["life"]=0
                        if not player["invincible"] and player["alive"]:
                            player["hp"]-=proj["dmg"]*self.players[proj["owner_conn"]]["scale"]    
                            if player["hp"]<=0:
                                player["alive"]=False
                                player["hp"]=0

        self.projectile[:]=[p for p in self.projectile if p["life"]]
        self.broadcast_world_state()

    def use_transform(self,skill,sk_count,p):
        if skill["name"]=="shrink":
            if sk_count>0:
                #p["state"]="transform"
                p["scale"]*=skill["scale"]
            else:
                #p["state"]="normal"
                p["scale"]/=skill["scale"]


    def spawn_sowrd(self,skill,wx,wy,p,D):
        if skill["name"]=="bigsword":
            pass



    def use_movement_skill(self,skill,wx,wy,sk_count,p):
        skill_name=skill["name"]
        if skill_name=="dash":
            if sk_count%2:
                p["state"]="movement"
                p["invincible"]=True
                p["dashvx"]=wx*skill["speed"]
                p["dashvy"]=wy*skill["speed"]
                p["dash_hit"]=False
            else:
                p["vx"]=p["dashvx"]*0.2
                p["vy"]=p["dashvy"]*0.2   
                p["state"]="normal" 
                p["invincible"]=False  
                p["dash_hit"]=True  
            
    def spawn_projectile(self,p,skill,wx,wy,skill_id):
        
        a=skill.get("a",0)
        proj={
            "id":self.next_projectile_id,
            "x":p["x"]+p["pw"]/2,
            "y":p["y"]+p["ph"]/2,
            "vx":skill["speed"]*wx,
            "vy":skill["speed"]*wy,
            "ax":a*wx,
            "ay":a*wy,
            "dmg":skill["dmg"],
            "owner":p["id"],
            "skill_id":skill_id,
            "life":skill.get("bounces",1),
            "r":skill.get("hitbox_rad",None),
            "owner_conn":p["conn"]
        }
        self.next_projectile_id+=1
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
                "skill_cd":p["skill_cd"],
                "hp":p["hp"],
                "pw":p["pw"],
                "ph":p["ph"]
            })
        for proj in self.projectile:
            snapshot_proj.append({
                "id":proj["id"],
                "x":proj["x"],
                "y":proj["y"],
                "owner":proj["owner"],
                "skill_id":proj["skill_id"],
                "life":proj["life"],
                "r":proj["r"]
            })
        self.broadcast({
            "type":"world_state",
            "data":{
                "players":snapshot_player,
                "proj":snapshot_proj
            }
        })