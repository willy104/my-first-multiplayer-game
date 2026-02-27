import socket
import threading
import json
import struct
import os
from map_creat import creat_map
from constnums import P_SPEED,GRAVITY,SKILLS

class GameClient(threading.Thread):
    def __init__(self,ip,port=5555):
        super().__init__(daemon=True)
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.connect((ip,port))
        self.running=True
        
        self.gameobjects=[]
        self.player_id=None
        self.can_move=False
        self.game_started=False
        self.players={}
        self.map_data=None
        print("connected to server")
    @property
    def me(self):
        return self.players.get(self.player_id)
    def run(self):
        try:
            while self.running:
                try:
                    raw_len=self.sock.recv(4)
                    if not raw_len:
                        break
                    msg_len=struct.unpack(">I",raw_len)[0]
                    data=self.receive_fixed(msg_len)

                    if data:
                        msg=json.loads(data.decode())
                        

                    print(f"server msg: {msg}")
                    self.handle_msg(msg)

                except Exception as e:
                    print("client error",e)
            print("disconnect")
        except Exception as e:
            print("client error",e)
    def receive_fixed(self,length):
        data=b""
        while len(data)<length:
            chunk=self.sock.recv(length-len(data))
            if not chunk:
                return None
            data+=chunk
        return data

    def send(self,msg_dict):
        data=json.dumps(msg_dict).encode()
        packet=struct.pack(">I",len(data))+data
        self.sock.sendall(packet)
    
    def close(self):
        self.running=False
        self.sock.close()
    
    def handle_msg(self,msg):
        msg_type=msg["type"]

        if msg_type=="world_state":
            self.handle_world_state(msg["data"])

        elif msg_type=="assign_id":
            self.player_id=msg["id"]
            self.ensure_player(self.player_id)

        elif msg_type=="current_players":
            for pdata in msg["data"]:
                pid=pdata["player_id"]
                self.players[pid]={   
                    "x":0,
                    "y":0,
                    "vx":P_SPEED,
                    "vy":0,
                    "ax":0,
                    "ay":0,
                    "skills":pdata["skills"],
                    "skill_cd":[0,0,0],
                    "hp":500,
                    "ready":pdata["ready"],
                    "connected":True
                }
        elif msg_type=="player_update":
            data=msg["data"]
            pid=data["player_id"]
            if "skills" in data:
                self.players[pid]["skills"]=data["skills"]
            if "ready" in data:
                self.players[pid]["ready"]=data["ready"]
        elif msg_type=="player_join":
            pid=msg["data"]["player_id"]
            self.ensure_player(pid)

        elif msg_type=="gamestart":
            self.game_started=True
            self.on_game_start()
        elif msg_type=="load_map":
            try:
                mapname=msg["data"]["map"]
                self.load_map(mapname)
            except Exception as e:
                print("map load error",e)
    def load_map(self,mapname):
        base_dir=os.path.dirname(os.path.abspath(__file__))
        path=os.path.join(base_dir,"..","assets","map",mapname)
        path=os.path.normpath(path)
        with open(path,"r",encoding="utf-8")as f:
            self.map_data=json.load(f)
        

        self.mapSurf=creat_map(self.map_data,path)
    def ensure_player(self,pid):
        if pid not in self.players:
            self.players[pid]={
                "connected":True,
                "x":0,
                "y":0,
                "vx":P_SPEED,
                "vy":0,
                "ax":0,
                "ay":0,
                "skills":[1,2,3],
                "skill_cd":[0,0,0],
                "hp":500,
                "ready":False    
            }
    def handle_world_state(self,data):
        for pdata in data["players"]:
            pid=pdata["player_id"]
            self.ensure_player(pid)

            self.players[pid]["x"]=pdata["x"]
            self.players[pid]["y"]=pdata["y"]
            self.players[pid]["skill_cd"]=pdata["skill_cd"]
            


            obj=next((o for o in self.gameobjects if o.get("pid")==pid),None)
            if obj:
                obj["x"]=pdata["x"]
                obj["y"]=pdata["y"]
                obj["dx"]=pdata["dx"]
                obj["dy"]=pdata["dy"]
            else:
                self.gameobjects.append({
                    "type":"player",                                        
                    "pid":pid,                
                    "x":pdata["x"],
                    "y":pdata["y"],
                    "dx":pdata["dx"],
                    "dy":pdata["dy"],
                    "img":None
                })
        proj_ids=set()
        for proj_data in data["proj"]:
            proj_id=proj_data["id"]
            proj_ids.add(proj_id)

            obj=next((o for o in self.gameobjects 
                      if o.get("type")=="projectile" and o.get("id")==proj_id),None)

            if obj:
                obj["x"]=proj_data["x"]
                obj["y"]=proj_data["y"]
                obj["life"]=proj_data["life"]
            else:
                self.gameobjects.append({
                    "type":"projectile",
                    "id":proj_data["id"],
                    "x":proj_data["x"],
                    "y":proj_data["y"],
                    "r":proj_data["r"],
                    "owner":proj_data["owner"],
                    "skill_id":proj_data["skill_id"],
                    "img":None,
                    "life":proj_data["life"],
                    "hitbox":SKILLS[proj_data["skill_id"]-1].get("hitbox")
                })
        self.gameobjects=[o for o in self.gameobjects 
                          if o.get("type") != "projectile" 
                          or o.get("id") in proj_ids
                        ]
    def on_game_start(self):
        self.can_move=True


        