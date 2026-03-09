import pygame
from input_box import InputBox
from host import GameServer
from guest import GameClient
from constnums import SKILLS

pygame.init()
pygame.mouse.set_visible(False)


winW,winH=960,640

screen=pygame.display.set_mode((winW,winH))

mainmenuSurf=pygame.Surface((winW,winH))
readySurf=pygame.Surface((winW,winH))
gameSurface=pygame.Surface((winW,winH))

clock=pygame.time.Clock()

pygame.display.set_caption("game")


#載入
mainmenuimg=pygame.image.load("assets/images/menus/mainmenu.png").convert()
triangleimg=pygame.image.load("assets/images/triangle.png").convert_alpha()
creatchartimg=pygame.image.load("assets/images/charts/creatchart.png").convert_alpha()
joinchartimg=pygame.image.load("assets/images/charts/joinchart.png").convert_alpha()
readymenuimg=pygame.image.load("assets/images/menus/readymenu1.png").convert()

targetlogo=pygame.image.load("assets/images/targetlogo.png").convert_alpha()
waiting_text=pygame.image.load("assets/images/texts/waiting_for_p2.png").convert_alpha()
choose_text=pygame.image.load("assets/images/texts/choose_your_skills.png").convert_alpha()
readycancel_text=pygame.image.load("assets/images/texts/readycancel.png").convert_alpha()
starting_text=pygame.image.load("assets/images/texts/starting_in.png").convert_alpha()
skillbox=pygame.image.load("assets/images/skill_box.png").convert()
p1_text=pygame.image.load("assets/images/texts/p1.png").convert_alpha()
p2_text=pygame.image.load("assets/images/texts/p2.png").convert_alpha()
you_hint=pygame.image.load("assets/images/texts/youhint.png").convert_alpha()
pready=pygame.image.load("assets/images/texts/pready.png").convert_alpha()
healthbarimg=pygame.image.load("assets/images/texts/healthbar.png").convert_alpha()

p_yellow=pygame.image.load("assets/images/players/player_yellow.png").convert_alpha()
p_green=pygame.image.load("assets/images/players/player_green.png").convert_alpha()
rp_green=pygame.transform.flip(p_green,True,False)

fireballicon=pygame.image.load("assets/images/icons/fireballicon.png").convert_alpha()
bounceballicon=pygame.image.load("assets/images/icons/bounceballicon.png").convert_alpha()
dashicon=pygame.image.load("assets/images/icons/dashicon.png").convert_alpha()
lanceicon=pygame.image.load("assets/images/icons/lanceicon.png").convert_alpha()

player1img=pygame.image.load("assets/images/gameobjects/player1img.png").convert()
player2img=pygame.image.load("assets/images/gameobjects/player2img.png").convert()
p_eye=pygame.image.load("assets/images/gameobjects/ceyes.png").convert_alpha()

font=pygame.font.Font("assets/fonts/PixelOperator8.ttf",23)



open_chart=False
screen_state="main menu"
focused_index=0
input_box=[]
icons=[fireballicon,bounceballicon,dashicon,lanceicon,
       fireballicon,bounceballicon,dashicon,lanceicon,
       fireballicon,bounceballicon,dashicon,lanceicon,
       fireballicon,bounceballicon,dashicon,lanceicon,
       fireballicon,bounceballicon,dashicon,lanceicon,
       fireballicon,bounceballicon,dashicon,lanceicon]
player=None



def host_create_chart():
    global input_box,focused_index
    input_box=[InputBox(pygame.Rect(360,260,238,28),"room name"),
                  InputBox(pygame.Rect(360,330,238,28),"password"),
                  InputBox(pygame.Rect(358,398,242,16),"confirm",True),
                  InputBox(pygame.Rect(358,420,242,16),"cancel",True)]
    focused_index=0
    input_box[focused_index].active=True
def join_chart():
    global input_box,focused_index
    input_box=[InputBox(pygame.Rect(360,260,238,28),"roo, ip"),
               InputBox(pygame.Rect(358,420,242,16),"confirm",True)]
    focused_index=0
    input_box[focused_index].active=True

ty=0
chart=False
creatchartrect=creatchartimg.get_rect(center=(winW//2,winH//2))
joinchartrect=joinchartimg.get_rect(center=(winW//2,winH//2))
def main_menu():
    global ty,chart,input_box,open_chart
    mainmenuSurf.blit(mainmenuimg,(0,0))
    keys=pygame.key.get_pressed()
    if open_chart or chart:
        if ty==0:
            if not chart:
                host_create_chart()
            mainmenuSurf.blit(creatchartimg,creatchartrect)
        if ty==1:
            if not chart:
                join_chart()
            mainmenuSurf.blit(joinchartimg,joinchartrect)
        chart=True
        open_chart=False
    else:
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            ty=0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            ty=1
        mainmenuSurf.blit(triangleimg,(415,294+ty*34))
    
now_t=0

def ready_menu():
    if not player or player.player_id is None:
        return
    global now_t,rx,ry,screen_state
    readySurf.blit(readymenuimg,(0,0))
    readySurf.blit(skillbox,(95,480))
    now_t=len(player.players)
                
    readySurf.blit(p_yellow,(152,380))
    readySurf.blit(p1_text,(164,280))
    if now_t==2:
        readySurf.blit(choose_text,(0,0))
        readySurf.blit(rp_green,(738,380))
        readySurf.blit(p2_text,(756,280))
        readySurf.blit(readycancel_text,(0,0))
        readySurf.blit(skillbox,(681,480))
    else:
        readySurf.blit(waiting_text,(0,0))
    if player.player_id==1:
        for i,j in enumerate(player.me["skills"]):
            readySurf.blit(icons[j-1],(98+i*60,483))
        readySurf.blit(you_hint,(156,320))
    else:
        for i,j in enumerate(player.me["skills"]):
            readySurf.blit(icons[j-1],(684+i*60,483))
        readySurf.blit(you_hint,(744,320))

    for pid,pdata in player.players.items():
        if pdata["ready"] :
            if pid==1:
                readySurf.blit(pready,(89,200))
            else:
                readySurf.blit(pready,(675,200))
    skrect=pygame.Rect(358+rx*60,100+ry*60,62,62)
    for i in range(0,6):
        for j in range(0,4):
            readySurf.blit(icons[i*4+j],(361+j*60,103+i*60))
    
    pygame.draw.rect(readySurf,(180,255,255),skrect,6)
    if player.game_started:
        screen_state="in game"
        load_skill_img()

rx,ry=0,0

def select_skill(event):
    global rx,ry,player
    if event.type==pygame.KEYDOWN:
        if len(player.players)>=1 and event.key==pygame.K_SPACE:#測試用
            player.send({"type":"ready",
                        "data":{
                            "value":not player.me["ready"]
                        }})
        else:
            if (event.key==pygame.K_w or event.key==pygame.K_UP) and ry>0:
                ry-=1
            if (event.key==pygame.K_s or event.key==pygame.K_DOWN) and ry<5:
                ry+=1
            if (event.key==pygame.K_a or event.key==pygame.K_LEFT) and rx>0:
                rx-=1
            if (event.key==pygame.K_d or event.key==pygame.K_RIGHT) and rx<3:
                rx+=1
            if event.key==pygame.K_1:
                
                skill_id=4*ry+rx+1
                if player.me["skills"][0]!=skill_id:
                    player.send({"type":"select_skill",
                                "data":{
                                    "skill_id":skill_id,
                                    "slot":1
                                }})
            if event.key==pygame.K_2:
                skill_id=4*ry+rx+1
                if player.me["skills"][1]!=skill_id:
                    player.send({"type":"select_skill",
                                "data":{
                                    "skill_id":skill_id,
                                    "slot":2
                                }})
            if event.key==pygame.K_3:
                skill_id=4*ry+rx+1
                if player.me["skills"][2]!=skill_id:
                    player.send({"type":"select_skill",
                                "data":{
                                    "skill_id":skill_id,
                                    "slot":3
                                }})


def handle_confirm():
    global screen_state,server,player
    if ty:
        #ip=input_box[0].text
        ip="25.22.201.174"
        #ip="25.4.29.65"
        player=GameClient(ip)
        if player:
            screen_state="ready"
            player.start()
    else:
        room_name=input_box[0].text
        room_password=input_box[1].text

        server=GameServer(room_name,room_password)
        server.start()
        player=GameClient("127.0.0.1")
        player.start()
        screen_state="ready"

skill_img={}
def load_skill_img():
    global skill_img
    skill_img={}

    used_skills=set()

    for pid,pdata in player.players.items():
        for skill_id in pdata["skills"]:
            used_skills.add(skill_id)

    for skill_id in used_skills:
        if SKILLS[skill_id-1]["img"]:
            path=f"assets/images/gameobjects/skill{skill_id}img.png"
            skill_img[skill_id]=pygame.image.load(path).convert_alpha()

def draw_target_logo():
    global mx,my
    tar_rect=targetlogo.get_rect(center=(mx,my))
    gameSurface.blit(targetlogo,tar_rect)

gameobjects=[]
def draw_game_objects():
    gameSurface.fill((119,221,255))
    if player.mapSurf:
        gameSurface.blit(player.mapSurf,(-32,-32))
    for obj in player.gameobjects:
        if obj['type']=="player" and obj["img"] is None:
            if obj["pid"]==1:
                obj["img"]=player1img
            else:
                obj["img"]=player2img
            
        if obj["type"]=="projectile" and obj["hitbox"]=="circle":
            r=obj.get("r",5)
            pcolor=(100,100,255) if obj["owner"]==player.player_id else (255,50,50)
            pygame.draw.circle(gameSurface,pcolor,(int(obj["x"]),int(obj["y"])),r)
        '''if obj['type']=="projectile" and obj["img"] is None:
            obj["img"]=skill_img.get(obj["skill_id"])'''
        
        if obj["img"] is not None:
            gameSurface.blit(obj["img"],(obj["x"],obj["y"]))

        if obj['type']=="player":
            obj["dx"]=min(4,max(obj["dx"],-4))
            obj["dy"]=min(5,max(obj["dy"],-7))
            p_eye_rect=p_eye.get_rect(center=(obj["x"]+16+obj["dx"],obj["y"]+16+obj["dy"]))
            gameSurface.blit(p_eye,p_eye_rect)
    gameSurface.blit(healthbarimg,(0,0))
    if len(player.players)>=2:
        for i in range(1,3):
            hp=player.players[i].get("hp")
            hptxt=font.render(f"{hp}",False,(0,0,0))
            gameSurface.blit(hptxt,(13+(i-1)*870,40))

spacedown=False
mx,my=0,0
def move_inputs(): 
    global spacedown,mx,my
    keys=pygame.key.get_pressed()
    mx,my=pygame.mouse.get_pos()
    move_x=0
    jump=False

    skill_key=None

    if keys[pygame.K_a]:
        move_x-=1
    if keys[pygame.K_d]:
        move_x+=1
    if keys[pygame.K_SPACE]:
        if not spacedown:
            spacedown=True
            jump=True
    else:
        spacedown=False
    
    if keys[pygame.K_q]:
        skill_key=1
    elif keys[pygame.K_w]:
        skill_key=2
    elif keys[pygame.K_e]:
        skill_key=3
    

    player.send({
        "type":"inputs",
        "data":{
            "mx":mx,
            "my":my,
            "dir_x":move_x,
            "jump":jump,
            "skill_key":skill_key,
        }
    })


def main():
    global input_box,focused_index,chart,open_chart 
    running=True
    dt=0
    while running:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
            if screen_state =="main menu" and event.type==pygame.KEYDOWN:
                if event.key==pygame.K_SPACE and not chart:
                    open_chart=True
                if input_box:
                    if event.key==pygame.K_DOWN:
                        input_box[focused_index].active=False
                        focused_index=(focused_index+1)%len(input_box)
                        input_box[focused_index].active=True
                    elif event.key==pygame.K_UP:
                        input_box[focused_index].active=False
                        focused_index=(focused_index-1)%len(input_box)
                        input_box[focused_index].active=True
                    if  event.key==pygame.K_RETURN: 
                        if focused_index<len(input_box)-1 and not input_box[focused_index].is_button:
                            input_box[focused_index].active=False
                            focused_index+=1
                            input_box[focused_index].active=True
                    if  event.key==pygame.K_ESCAPE:
                        input_box=[]
                        focused_index=0
                        chart=False
                        open_chart=False
                    if event.key==pygame.K_SPACE:
                        if chart:
                            if input_box[focused_index].is_button:
                                name=input_box[focused_index].name
                                if name=="confirm":
                                    handle_confirm()
                                elif name=="cancel":
                                    input_box=[]
                                    focused_index=0
                                    chart=False
                                    open_chart=False
            if screen_state=="in game":
                pass
            elif screen_state=="main menu" and input_box :
                input_box[focused_index].handle_event(event)
            elif screen_state=="ready":
                select_skill(event)



        screen.fill((0,0,0))


        if screen_state=="main menu":
            main_menu()
            if input_box:
                for box in input_box:
                    box.draw(mainmenuSurf)
            screen.blit(mainmenuSurf,(0,0))
        elif screen_state=="ready":
            ready_menu()
            screen.blit(readySurf,(0,0))
        elif screen_state=="in game":
            move_inputs()
            draw_game_objects()
            draw_target_logo()
            screen.blit(gameSurface,(0,0))


        pygame.display.flip()
        dt=clock.tick(60)/1000

main()
pygame.quit()
