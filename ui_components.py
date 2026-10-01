"""Small offline Pygame UI primitives, navigation and stable status messages."""
from dataclasses import dataclass
import pygame
from space_art import skin, gradient, contour

BG = (12, 7, 48)
PANEL = (24, 97, 177)
CYAN = (83, 240, 255)
RED = (255, 159, 180)
INK = (251, 250, 255)
MUTED = (235, 234, 255)
BORDER = (54, 163, 231)
GOLD = (255, 225, 121)


@dataclass
class Button:
    rect: pygame.Rect
    action: str
    enabled: bool


class StableMessage:
    def __init__(self):
        self.text = self.candidate = ''
        self.elapsed = 0.0

    def update(self, text, dt, urgent=False):
        if text != self.candidate:
            self.candidate, self.elapsed = text, 0.0
        self.elapsed += dt
        if urgent or not self.text or self.elapsed >= 0.45:
            self.text = text
        return self.text


class Canvas:
    def __init__(self, surface):
        self.surface = surface
        # Pygame's redistributable default font is bundled by its PyInstaller hook.
        self.fonts = {size: pygame.font.Font(None, size) for size in (18, 20, 22, 24, 28, 32, 40, 48, 60, 84, 98, 112)}
        self.buttons = []
        self.focus = None
        self.scene = None
        self.pointer = (-1, -1)
        self.pressed = None
        self.key_pressed = False
        self.press_until = 0
        self.titles = {}

    def begin(self, scene, pointer):
        if scene != self.scene:
            self.focus = None
            self.pressed = None
            self.key_pressed = False
        self.scene, self.pointer = scene, pointer
        self.buttons.clear()

    def text(self, value, pos, size=28, color=INK, center=False):
        image = self.fonts[size].render(str(value), True, color)
        rect = image.get_rect(midtop=pos) if center else image.get_rect(topleft=pos)
        self.surface.blit(image, rect)
        return rect

    def title(self, value, pos, size=60, lavender=False, center=False):
        key = (value,size,lavender)
        if key not in self.titles:
            font = pygame.font.Font(None,size)
            font.set_bold(True)
            font.set_italic(not lavender)
            mask = font.render(value,True,(255,255,255))
            face = gradient(mask.get_size(), (246,245,255) if lavender else (22,179,255),
                            (174,167,239) if lavender else (0,243,244))
            face.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
            result = pygame.Surface((mask.get_width()+14,mask.get_height()+14),pygame.SRCALPHA)
            outline = font.render(value,True,(26,15,85))
            for dx,dy in ((0,2),(4,2),(2,0),(2,4)):
                result.blit(outline,(dx,dy))
            depth = font.render(value,True,(93,76,169) if lavender else (17,73,173))
            for offset in range(10,0,-1):
                result.blit(depth,(offset+2,offset+2))
            result.blit(face,(2,2))
            self.titles[key]=result
        result=self.titles[key]
        rect=result.get_rect(midtop=pos) if center else result.get_rect(topleft=pos)
        self.surface.blit(result,rect)
        return rect

    def wrap(self, value, rect, size=24, color=MUTED):
        rect = pygame.Rect(rect)
        y, line = rect.y, ''
        for word in str(value).split():
            trial = f'{line} {word}'.strip()
            if self.fonts[size].size(trial)[0] > rect.width and line:
                self.text(line, (rect.x, y), size, color)
                y += self.fonts[size].get_linesize() + 4
                line = word
            else:
                line = trial
        if line:
            self.text(line, (rect.x, y), size, color)
        return y + self.fonts[size].get_linesize()

    def panel(self, rect, color=PANEL):
        rect=pygame.Rect(rect)
        self.surface.blit(skin(rect.size,'panel' if color==PANEL else 'quiet'),rect)

    def button(self, label, rect, action, primary=False, enabled=True):
        rect = pygame.Rect(rect)
        self.buttons.append(Button(rect, action, enabled))
        if self.focus is None and enabled:
            self.focus = action
        hover = enabled and rect.collidepoint(self.pointer)
        kind = 'disabled' if not enabled else 'orange' if primary else 'lavender' if action=='pause' else 'cyan'
        pressed = enabled and (self.pressed==action or (self.key_pressed and self.focus==action) or
                               (hover and pygame.time.get_ticks()<self.press_until))
        visible = rect.inflate(-6,-4).move(0,4) if pressed else rect
        self.surface.blit(skin(visible.size,kind,'hover' if hover else 'normal'),visible)
        if self.focus == action and enabled:
            pygame.draw.lines(self.surface, INK, True, contour(rect.inflate(4,4)), 2)
        size=28
        while size>18 and self.fonts[size].size(label)[0]>rect.width-24:
            size=next(n for n in (24,22,20,18) if n<size)
        self.text(label, (visible.centerx, visible.y + (visible.height-self.fonts[size].get_height())//2-2),
                  size, (91,41,32) if primary and enabled else (27,24,85) if enabled else (215,224,242), center=True)

    def pointer_down(self, position):
        self.pressed = next((b.action for b in self.buttons if b.enabled and b.rect.collidepoint(position)),None)

    def pointer_up(self, position):
        pressed,self.pressed=self.pressed,None
        if pressed:
            for button in self.buttons:
                if button.action==pressed and button.enabled and button.rect.collidepoint(position):
                    self.focus=pressed
                    return pressed
        return None

    def click(self, position):
        for button in self.buttons:
            if button.enabled and button.rect.collidepoint(position):
                self.focus = button.action
                self.press_until = pygame.time.get_ticks()+110
                return button.action
        return None

    def navigate(self, key, reverse=False):
        enabled = [b.action for b in self.buttons if b.enabled]
        if not enabled:
            return None
        if self.focus not in enabled:
            self.focus = enabled[0]
        if key in (pygame.K_TAB, pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
            step = -1 if reverse or key in (pygame.K_UP, pygame.K_LEFT) else 1
            self.focus = enabled[(enabled.index(self.focus) + step) % len(enabled)]
        elif key == pygame.K_RETURN:
            return self.focus
        return None


def progress(surface, rect, value, color=CYAN):
    rect = pygame.Rect(rect)
    rect.height=max(8,rect.height)
    pygame.draw.rect(surface,(94,86,174),rect,border_radius=rect.height//2)
    pygame.draw.rect(surface,(196,209,255),rect,1,border_radius=rect.height//2)
    inner=rect.inflate(-4,-4)
    width = round(inner.width * max(0, min(1, value)))
    if width:
        fill=pygame.Rect(inner.x,inner.y,width,inner.height)
        pygame.draw.rect(surface,(255,169,10),fill,border_radius=inner.height//2)
        pygame.draw.line(surface,(255,240,150),fill.topleft,(fill.right-1,fill.top),1)


def gesture_icon(surface, kind, origin, color):
    """Consistent 28px line icons, no platform-specific emoji or image downloads."""
    x, y = origin
    if kind == 'shield':
        vertices=[(x,y),(x+22,y),(x+20,y+17),(x+11,y+26),(x+2,y+17)]
        pygame.draw.polygon(surface,(71,95,190),vertices)
        pygame.draw.polygon(surface,color,vertices,2)
        pygame.draw.polygon(surface,(179,249,255),[(x+4,y+4),(x+10,y+4),(x+10,y+18),(x+6,y+14)])
    elif kind == 'fire':
        pygame.draw.polygon(surface,(239,130,27),[(x+16,y-1),(x+2,y+15),(x+10,y+15),(x+7,y+27),(x+23,y+9),(x+15,y+9)])
        pygame.draw.lines(surface,(255,239,163),False,[(x+16,y-1),(x+2,y+15),(x+10,y+15)],2)
    else:
        pygame.draw.rect(surface, (231,223,255), (x+3, y+1, 6, 24), border_radius=2)
        pygame.draw.rect(surface, (177,164,241), (x+15, y+1, 6, 24), border_radius=2)
