"""Draw the unchanged combat simulation directly in viewport coordinates.

Positions and hitbox bounds are projected, but fonts, strokes and details are
rendered at their native aspect ratio rather than stretching a world bitmap.
"""
import math
import pygame
from effects import Effects
from space_art import gradient
from ui_components import INK, CYAN, GOLD, RED


class ArenaView:
    def __init__(self):
        self.effects = Effects()
        self.background = None
        self.font = pygame.font.Font(None, 22)

    @staticmethod
    def project(point, arena, viewport):
        return (viewport.x+(point[0]-arena.x)*viewport.width/arena.width,
                viewport.y+(point[1]-arena.y)*viewport.height/arena.height)

    def draw(self, game, screen, viewport, dt, reduced):
        self.effects.update(game, dt, reduced)
        arena = game.arena
        point = lambda x,y: self.project((x,y),arena,viewport)
        def rect(world):
            x,y=point(world.x,world.y)
            return pygame.Rect(round(x),round(y),max(1,round(world.width*viewport.width/arena.width)),
                               max(1,round(world.height*viewport.height/arena.height)))
        def polygon(r, coords, color):
            vertices=[(r.x+x*r.width,r.y+y*r.height) for x,y in coords]
            pygame.draw.polygon(screen,color,vertices)
            return vertices
        if self.background is None or self.background.get_size()!=viewport.size:
            self.background=gradient(viewport.size,(13,12,47),(33,19,69))
        screen.blit(self.background,viewport)
        screen.set_clip(viewport)
        for i in range(55):
            x=viewport.x+(i*173+31)%viewport.width
            y=viewport.y+(i*79+(0 if reduced else game.elapsed)*(5+i%4))%viewport.height
            pygame.draw.circle(screen,(67,58,110),(round(x),round(y)),1)
        for bullet in game.bullets:
            r=rect(bullet.rect())
            pygame.draw.rect(screen,(17,124,169),r.inflate(4,8),border_radius=4)
            pygame.draw.rect(screen,CYAN,r,border_radius=3)
            pygame.draw.line(screen,INK,r.midtop,r.midbottom,2)
        for rock in game.obstacles:
            r=rect(rock.rect())
            flash=rock.hit_flash>0
            if rock.kind=='armored':
                pygame.draw.rect(screen,(134,78,24),r,border_radius=8)
                pygame.draw.rect(screen,INK if flash else (255,203,74),r,3,border_radius=8)
                pygame.draw.rect(screen,(255,157,16),r.inflate(-12,-10),border_radius=5)
                label=self.font.render(str(rock.hp),True,(72,37,44))
                screen.blit(label,label.get_rect(center=r.center))
                for dx in (7,r.width-9):
                    pygame.draw.circle(screen,(255,243,182),(r.x+dx,r.centery),2)
            elif rock.kind=='zigzag':
                polygon(r,[(0,.5),(.5,0),(1,.5),(.5,1)],INK if flash else (177,132,242))
                polygon(r,[(0,.5),(.5,.4),(1,.5),(.5,1)],(95,53,168))
                pygame.draw.circle(screen,(108,247,255),r.center,3)
            else:
                shape=[(.04,.31),(.25,.05),(.6,.02),(.99,.47),(.82,.86),(.3,.98),(0,.69)]
                vertices=polygon(r,shape,INK if flash else (168,99,143))
                polygon(r,[(.04,.31),(.25,.05),(.6,.02),(.42,.45)],(224,151,180))
                polygon(r,[(.42,.45),(.99,.47),(.82,.86),(.3,.98)],(111,60,118))
                pygame.draw.ellipse(screen,(83,47,96),(r.x+r.width*.23,r.y+r.height*.32,r.width*.19,r.height*.28))
                pygame.draw.aalines(screen,RED,True,vertices)
        if game.boss:
            r=rect(game.boss.rect())
            pygame.draw.ellipse(screen,(130,107,211),r)
            pygame.draw.ellipse(screen,(201,185,247),(r.x+r.width*.25,r.y,r.width*.5,r.height*.66))
            pygame.draw.ellipse(screen,INK if game.boss.hit_flash else (98,55,176),(r.x,r.y+r.height*.5,r.width,r.height*.5))
            for i in range(5):
                pygame.draw.circle(screen,(255,145,158),(round(r.x+(i+1)*r.width/6),round(r.y+r.height*.73)),3)
        for x in game.warning_lanes:
            if game.boss_phase in ('warning','active'):
                lane=rect(pygame.Rect(x-28,arena.top+170 if game.boss_phase=='warning' else arena.top+160,56,arena.height))
                pygame.draw.rect(screen,GOLD if game.boss_phase=='warning' else (255,104,151),lane,2 if game.boss_phase=='warning' else 0)
                if game.boss_phase=='warning':
                    for y in range(lane.top,viewport.bottom,22):
                        pygame.draw.line(screen,GOLD,(lane.x+8,y),(lane.right-8,y+8),1)
                else:
                    pygame.draw.rect(screen,INK,lane.inflate(-lane.width*.65,0))
        for x,y,vx,speed in game.fan_paths:
            travel=(arena.bottom-y)/speed
            pygame.draw.line(screen,GOLD,point(x,y),point(x+vx*travel,arena.bottom),1)
        for bullet in game.hostile_bullets:
            p=point(bullet.x,bullet.y)
            pygame.draw.circle(screen,(255,110,153),p,7)
            pygame.draw.circle(screen,(255,232,144),p,3)
        player=rect(game.player)
        if not game.invulnerable or int(game.invulnerable*12)%2:
            flame=8 if reduced else 8+3*math.sin(game.elapsed*31)
            polygon(player,[(.4,1),(.5,1+flame/player.height),(.6,1)],(255,175,39))
            polygon(player,[(.5,0),(0,1),(.4,.72),(.5,.93),(.6,.72),(1,1)],(165,155,235))
            polygon(player,[(.5,0),(.4,.72),(.5,.93),(.6,.72)],(229,225,255))
            pygame.draw.ellipse(screen,(19,137,207),(player.centerx-5,player.y+7,10,12))
            pygame.draw.ellipse(screen,(129,251,255),(player.centerx-4,player.y+8,4,7))
        if game.shield_remaining>0:
            pygame.draw.ellipse(screen,CYAN,player.inflate(27,25),2)
        for x,y,_,_,life,color in self.effects.particles:
            pygame.draw.circle(screen,color,point(x,y),max(1,int(life*6)))
        if game.invulnerable>.95:
            pygame.draw.rect(screen,RED,viewport.inflate(-6,-6),3,border_radius=14)
        screen.set_clip(None)
