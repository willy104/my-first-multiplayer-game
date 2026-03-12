P_SPEED=200
GRAVITY=1200
JUMP_CD=0.2
JUMP_SPEED=-500
MAX_JUMP_COUNT=2

SKILLS=[
{"name":"fireball","id":1,"cd":2.5,"dmg":50,"amount":3,"atkspeed":0.1,"aim":"tap","type":"projectile","speed":50,"a":2000,"hitbox":"circle","hitbox_rad":8,"img":True},#fireball
{"name":"bounceball","id":2,"cd":3,"dmg":20 ,"amount":6,"atkspeed":0.2,"aim":"tap","type":"projectile","speed":500,"hitbox":"circle","hitbox_rad":6,"bounces":5,"img":True},#bounceball
{"name":"dash","id":3,"cd":3.0,"dmg":30 ,"amount":2,"atkspeed":0.1,"aim":"tap","type":"movement","speed":1600,"img":False},#dash
{"name":"bigsword","id":4,"cd":3.0,"dmg":50 ,"amount":1,"atkspeed":1.0,"aim":"tap","type":"sword","speed":300,"img":True},#bigswordd
{"name":"shrink","id":5,"cd":4.0,"dmg":0 ,"amount":2,"atkspeed":2.0,"aim":"tap","type":"transform","scale":1.5,"img":True},
{"name":"sword_slash","id":6,"cd":3.0,"dmg":50 ,"amount":2,"atkspeed":0.05,"aim":"tap","type":"slash","img":True}#sword_slash
]