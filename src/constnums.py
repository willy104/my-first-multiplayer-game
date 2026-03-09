P_SPEED=200
GRAVITY=1200
JUMP_CD=0.2
JUMP_SPEED=-500
MAX_JUMP_COUNT=2

SKILLS=[
{"id":1,"cd":3.0,"dmg":50,"amount":3,"atkspeed":0.1,"aim":"tap","type":"projectile","speed":50,"a":2000,"hitbox":"circle","hitbox_rad":8,"img":True},#fireball
{"id":2,"cd":3.0,"dmg":10 ,"amount":5,"atkspeed":0.2,"aim":"tap","type":"projectile","speed":500,"hitbox":"circle","hitbox_rad":6,"bounces":5,"img":True},#bounceball
{"id":3,"cd":3.0,"dmg":0 ,"amount":2,"atkspeed":0.05,"aim":"tap","type":"movement","speed":1600,"img":False},#dash
{"id":4,"cd":3.0,"dmg":50 ,"amount":1,"atkspeed":0.2,"aim":"hold","type":"movement","speed":300,"img":True},#lance
{"id":5,"cd":3.0,"dmg":50 ,"amount":2,"atkspeed":0.05,"aim":"tap","type":"slash","img":True}#sword_slash
]