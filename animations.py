import pygame
import math

class Animation:
    def __init__(self, start_value, end_value, duration=0.3, easing='ease_out'):
        self.start_value = start_value
        self.end_value = end_value
        self.duration = duration * 60
        self.easing = easing
        self.current_time = 0
        self.is_playing = False
        
    def start(self):
        self.current_time = 0
        self.is_playing = True
        
    def update(self):
        if self.is_playing:
            self.current_time += 1
            if self.current_time >= self.duration:
                self.is_playing = False
                return self.end_value
            
            t = self.current_time / self.duration
            
            if self.easing == 'ease_out':
                t = 1 - (1 - t) ** 3
            elif self.easing == 'ease_in':
                t = t ** 3
            elif self.easing == 'ease_in_out':
                t = (t ** 2) / (t ** 2 + (1 - t) ** 2)
            elif self.easing == 'bounce':
                t = self.bounce_out(t)
                
            return self.start_value + (self.end_value - self.start_value) * t
        
        return self.end_value
    
    def bounce_out(self, t):
        if t < 1 / 2.75:
            return 7.5625 * t ** 2
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t ** 2 + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t ** 2 + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t ** 2 + 0.984375

class PulseAnimation:
    def __init__(self, target, scale=1.1, duration=0.2):
        self.target = target
        self.original_rect = target.rect.copy()
        self.scale = scale
        self.duration = duration * 60
        self.current_time = 0
        self.is_playing = False
        
    def start(self):
        self.current_time = 0
        self.is_playing = True
        
    def update(self):
        if self.is_playing:
            self.current_time += 1
            if self.current_time >= self.duration:
                self.is_playing = False
                self.target.rect = self.original_rect.copy()
                return
            
            t = self.current_time / self.duration
            if t < 0.5:
                scale = 1 + (self.scale - 1) * (t * 2)
            else:
                scale = self.scale - (self.scale - 1) * ((t - 0.5) * 2)
            
            center = self.target.rect.center
            new_width = int(self.original_rect.width * scale)
            new_height = int(self.original_rect.height * scale)
            self.target.rect = pygame.Rect(0, 0, new_width, new_height)
            self.target.rect.center = center

class FadeAnimation:
    def __init__(self, surface, start_alpha=0, end_alpha=255, duration=0.3):
        self.surface = surface
        self.start_alpha = start_alpha
        self.end_alpha = end_alpha
        self.duration = duration * 60
        self.current_time = 0
        self.is_playing = False
        
    def start(self):
        self.current_time = 0
        self.is_playing = True
        
    def update(self):
        if self.is_playing:
            self.current_time += 1
            if self.current_time >= self.duration:
                self.is_playing = False
                return self.end_alpha
            
            t = self.current_time / self.duration
            alpha = int(self.start_alpha + (self.end_alpha - self.start_alpha) * t)
            return alpha
        
        return self.end_alpha