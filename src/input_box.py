import pygame


class InputBox:
    def __init__(self,rect,name,is_button=False):
        self.rect=rect
        self.name=name
        self.active=False
        self.text=""
        self.is_button=is_button
        self.font=pygame.font.SysFont("None",28)
        self.color_active=(0,200,255)
        self.color_inactive=(120,120,120)
        self.text_color=(255,255,255)
        self.hind_color=(160,160,160)
    def handle_event(self,event):
        if event.type==pygame.KEYDOWN and self.active:
            if  self.is_button:
                pass
            else:
                if event.key==pygame.K_BACKSPACE:
                    self.text=self.text[:-1]
                else:
                    if event.unicode.isalnum():
                        if len(self.text)<15:
                            self.text+=event.unicode
    def update(self):
        pass
    def draw(self,nowsurface):
        border_color=self.color_active if self.active else self.color_inactive
        pygame.draw.rect(nowsurface,border_color,self.rect,2)

        if self.text:
            txt_surface=self.font.render(self.text,True,self.text_color)
        else:
            txt_surface=self.font.render(self.text,True,self.text_color)
        nowsurface.blit(txt_surface,(self.rect.x+8,self.rect.y+(self.rect.height-txt_surface.get_height())//2))