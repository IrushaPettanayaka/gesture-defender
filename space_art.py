"""Original procedural illustrations inspired by the supplied Freepik style sheet.

No reference pixels or EPS paths are embedded. Cached transparent shapes are
generated locally; text remains live. See ART_ATTRIBUTION.md for provenance.
"""
from functools import lru_cache
import math
import pygame


def gradient(size, top, bottom):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        color = tuple(round(a + (b-a)*t) for a, b in zip(top, bottom))
        pygame.draw.line(surface, color, (0, y), (size[0], y))
    return surface


def contour(rect, power=0.24):
    """A gently bowed superellipse: curved sides instead of a rounded rectangle."""
    r = pygame.Rect(rect)
    points = []
    for i in range(96):
        a = i * math.tau / 96
        c, s = math.cos(a), math.sin(a)
        x = math.copysign(abs(c)**power, c)
        y = math.copysign(abs(s)**power, s)
        points.append((r.centerx+x*r.width/2, r.centery+y*r.height/2 + x*2))
    return points


@lru_cache(maxsize=12)
def preview_mask(size):
    mask=pygame.Surface(size,pygame.SRCALPHA)
    pygame.draw.polygon(mask,(255,255,255),contour(pygame.Rect(0,0,*size).inflate(-2,-2),0.15))
    return mask


@lru_cache(maxsize=160)
def skin(size, kind='panel', state='normal'):
    """Supersampled, transparent, locally cached scalable panel/button skin."""
    w, h = size
    scale = 2
    output = pygame.Surface((w*scale, h*scale), pygame.SRCALPHA)
    palettes = {
        'panel': ((14,111,183), (35,72,167), (58,226,252), (26,22,98)),
        'quiet': ((24,87,147), (30,46,113), (58,155,210), (21,16,72)),
        'orange': ((255,192,13), (255,130,6), (255,233,109), (167,70,43)),
        'cyan': ((2,206,249), (0,137,232), (113,250,255), (31,53,147)),
        'lavender': ((244,237,255), (166,162,228), (255,255,255), (92,78,159)),
        'disabled': ((100,124,160), (65,84,132), (133,153,184), (41,43,94)),
    }
    top, bottom, edge, shadow = palettes[kind]
    if state == 'hover':
        top, bottom = [tuple(min(255, v+15) for v in c) for c in (top, bottom)]
    # Work in doubled coordinates for smooth curves at every runtime size.
    depth = 6 if kind not in ('panel', 'quiet') else 4
    r = pygame.Rect(3*scale, 2*scale, (w-6)*scale, (h-depth-4)*scale)
    path = contour(r, 0.3 if kind in ('orange','cyan','lavender','disabled') else 0.15)
    pygame.draw.polygon(output, shadow, [(x,y+depth*scale) for x,y in path])
    fill = gradient(output.get_size(), top, bottom)
    mask = pygame.Surface(output.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255,255,255), path)
    fill.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
    output.blit(fill, (0,0))
    shine = pygame.Surface(output.get_size(), pygame.SRCALPHA)
    pygame.draw.ellipse(shine, (218,250,255,28 if kind in ('panel','quiet') else 65),
                        (-w*scale//5, -h*scale//3, w*scale*1.2, h*scale*.88))
    if kind == 'orange':
        pygame.draw.polygon(shine, (255,250,115,52), [(w*.53*scale,0),(w*.68*scale,0),(w*.48*scale,h*scale),(w*.34*scale,h*scale)])
        pygame.draw.ellipse(shine, (255,243,80,110), (w*.1*scale,h*.67*scale,w*.86*scale,h*.21*scale))
    shine.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
    output.blit(shine,(0,0))
    pygame.draw.lines(output, edge, True, path, 2*scale)
    if w > 100 and h > 42:
        pygame.draw.ellipse(output, (244,255,255,245), (12*scale,8*scale,min(28,w*.09)*scale,5*scale))
        pygame.draw.circle(output, (226,255,255), (10*scale,19*scale), 2*scale)
        pygame.draw.ellipse(output, (168,252,255), ((w-28)*scale,(h-depth-10)*scale,14*scale,3*scale))
    return pygame.transform.smoothscale(output, size)


@lru_cache(maxsize=32)
def illustration(kind, size):
    """Create an individual transparent planet, saucer, rocket or asteroid."""
    s = pygame.Surface((400,400), pygame.SRCALPHA)
    if kind in ('planet','moon','orange_planet'):
        colors = ((70,95,201),(26,25,99),(139,146,242)) if kind=='moon' else ((240,76,132),(89,23,113),(255,150,189)) if kind=='planet' else ((255,185,12),(233,89,8),(255,232,107))
        base, dark, light = colors
        for radius in range(180,0,-1):
            t = radius/180
            color = tuple(round(a+(b-a)*t*.72) for a,b in zip(base,dark))
            pygame.draw.circle(s,color,(200,200),radius)
        pygame.draw.arc(s,light,(21,21,358,358),0.3,2.9,5)
        for x,y,r in ((113,109,28),(244,88,18),(277,201,31),(122,247,34),(214,295,23),(206,164,16),(302,277,12)):
            pygame.draw.ellipse(s,dark,(x-r,y-r,r*2,r*1.3))
            pygame.draw.arc(s,light,(x-r,y-r+4,r*2,r*1.3),3.2,5.5,3)
        pygame.draw.ellipse(s,(*light,150),(68,90,18,55))
    elif kind == 'ufo':
        pygame.draw.ellipse(s,(69,28,143),(31,222,338,61))
        pygame.draw.ellipse(s,(255,135,85),(105,219,206,45))
        pygame.draw.ellipse(s,(255,240,144),(124,227,169,28))
        pygame.draw.ellipse(s,(139,138,220),(109,118,186,139))
        pygame.draw.ellipse(s,(213,211,255),(119,121,149,105))
        pygame.draw.ellipse(s,(64,39,143),(26,191,350,76))
        pygame.draw.ellipse(s,(165,158,240),(26,183,350,58))
        pygame.draw.ellipse(s,(239,238,255),(43,183,280,24))
        for x,y in ((64,219),(120,235),(190,241),(266,231),(328,212)):
            pygame.draw.ellipse(s,(66,242,255),(x,y,23,9))
    elif kind == 'rocket':
        pygame.draw.polygon(s,(117,68,171),[(153,287),(188,395),(219,294)])
        pygame.draw.polygon(s,(255,172,24),[(171,282),(192,369),(213,282)])
        pygame.draw.polygon(s,(255,244,139),[(180,284),(193,333),(202,284)])
        pygame.draw.polygon(s,(101,84,186),[(147,182),(82,257),(80,309),(160,271)])
        pygame.draw.polygon(s,(169,170,237),[(239,180),(301,252),(304,310),(223,273)])
        pygame.draw.polygon(s,(87,67,150),[(136,272),(243,272),(229,305),(151,305)])
        pygame.draw.ellipse(s,(147,147,218),(123,48,135,251))
        pygame.draw.ellipse(s,(223,220,255),(129,51,95,229))
        pygame.draw.polygon(s,(162,166,236),[(129,119),(146,68),(190,20),(237,80),(253,128)])
        pygame.draw.polygon(s,(232,233,255),[(131,118),(152,69),(190,20),(182,99)])
        pygame.draw.circle(s,(67,61,156),(193,174),49)
        pygame.draw.circle(s,(42,214,250),(193,174),40)
        pygame.draw.circle(s,(19,147,218),(197,181),30)
        pygame.draw.ellipse(s,(162,255,255),(166,148,20,38))
        for x,y in ((193,124),(144,175),(242,175),(193,224)):
            pygame.draw.circle(s,(209,212,255),(x,y),4)
    else:
        points=[(82,147),(176,70),(292,112),(346,248),(230,328),(94,271),(58,205)]
        pygame.draw.polygon(s,(85,47,109),points)
        pygame.draw.polygon(s,(159,94,146),[points[0],points[1],points[2],(234,203),(129,214)])
        pygame.draw.polygon(s,(119,62,125),[points[2],points[3],points[4],(234,203)])
        pygame.draw.polygon(s,(211,136,178),[points[0],points[1],points[2],(175,131)])
        pygame.draw.ellipse(s,(86,46,106),(125,171,48,28))
    return pygame.transform.smoothscale(s,(size,size))


class SpaceBackdrop:
    def __init__(self, size):
        self.size = size
        self.background = gradient(size,(9,5,50),(55,9,79))
        self.quiet = gradient(size,(9,8,39),(24,15,60))

    def draw(self, target, elapsed, reduced=False, quiet=False, menu=False):
        target.blit(self.quiet if quiet else self.background,(0,0))
        w,h = self.size
        for i in range(84 if not quiet else 42):
            x,y = (i*193+31)%w, (i*107+53)%h
            color = (69,66,126) if quiet else (119,147,198)
            pygame.draw.circle(target,color,(x,y),1+i%2)
            if not quiet and i%13==0:
                pygame.draw.line(target,(168,217,244),(x-4,y),(x+4,y),1)
                pygame.draw.line(target,(168,217,244),(x,y-4),(x,y+4),1)
        if quiet:
            return
        t = 0 if reduced else elapsed
        objects = [('planet',248,(w-244,-112)),('moon',148,(-75,180)),('orange_planet',92,(w-117,h-123))]
        if menu:
            objects += [('moon',155,(1010,239)),('orange_planet',102,(748,563)),('ufo',248,(810,28)),('asteroid',126,(1145,523))]
        for i,(kind,size,pos) in enumerate(objects):
            target.blit(illustration(kind,size),(pos[0],pos[1]+math.sin(t*.7+i)*5))
