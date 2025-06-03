import time
import pygame
import random
import math

from .animation import Animation

_enemy_animation_cache = {}

class Enemy:
    def __init__(self, enemy_data):
        self.id = enemy_data['id']
        self.type = enemy_data['type']
        self.x = enemy_data['x']
        self.y = enemy_data['y']
        self.speed = enemy_data.get('speed', 1.5)
        self.max_health = 100
        self.health = enemy_data.get('health', enemy_data.get('max_health', 100))
        self.damage = enemy_data.get('damage', 10)
        self.prev_x = self.x
        self.prev_y = self.y
        self.has_moved = False
        self.state = "idle"
        self.is_moving = False
        self.last_damage_time = 0
        self.damage_flash_duration = 0.2
        self.animations = {}
        self.flip = False
        self.current_animation = None
        if not hasattr(self, 'sprite_base_path'):
            self.sprite_base_path = "client/assets/enemies/goblin"
        self._init_animations()
        self.change_state("idle")

    def _init_animations(self):
        anim_paths = {
            "idle": f"{self.sprite_base_path}/idle.png",
            "run": f"{self.sprite_base_path}/run.png",
            "attack": f"{self.sprite_base_path}/attack.png",
        }

        animation_specs = {
            "idle": (4, 0.2),
            "run": (8, 0.1),
            "attack": (8, 0.05),
        }

        for state, path in anim_paths.items():
            try:
                sprite_sheet = _enemy_animation_cache.get(path)
                if not sprite_sheet:
                    sprite_sheet = pygame.image.load(path).convert_alpha()
                    _enemy_animation_cache[path] = sprite_sheet
            except Exception as e:
                print(f"Failed to load {path}: {e}")
                sprite_sheet = pygame.Surface((64, 64), pygame.SRCALPHA)
            
            frames, duration = animation_specs[state]
            self.animations[state] = Animation(sprite_sheet, 150, 150, frames, duration)

    def change_state(self, new_state):
        if new_state in self.animations:
            if self.state != new_state:
                self.state = new_state
                self.current_animation = self.animations[new_state]
                self.current_animation.current_frame = 0
                self.current_animation.elapsed_time = 0
        else:
            print(f"Warning: Missing animation state {new_state} for {self.type}")

    def update(self, dt):
        self.has_moved = (self.x != self.prev_x) or (self.y != self.prev_y)
        self.prev_x = self.x
        self.prev_y = self.y
        if self.has_moved and self.state != "run":
            self.change_state("run")
        elif not self.has_moved and self.state != "idle":
            self.change_state("idle")
        if self.current_animation:
            self.current_animation.update(dt)

    def draw(self, screen, view_x=0, view_y=0):
        screen_x = self.x - view_x
        screen_y = self.y - view_y
        current_frame = self.animations[self.state].get_frame()
        if self.flip:
            current_frame = pygame.transform.flip(current_frame, True, False)
        screen.blit(current_frame, (screen_x, screen_y))
        sprite_height = current_frame.get_height()
        self.draw_health_bar(screen, screen_x + 30, screen_y + 40)

    def draw_health_bar(self, screen, x, y):
        bar_width = 50
        bar_height = 5
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, (255, 0, 0), 
                       (x, y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), 
                       (x, y, bar_width * health_ratio, bar_height))

    def take_damage(self, damage):
        self.health = max(0, self.health - damage)
        self.is_dead = self.health <= 0

class Goblin(Enemy):
    sprite_base_path = "client/assets/enemies/goblin"

    def __init__(self, enemy_data):
        enemy_data['type'] = 'goblin'
        enemy_data['max_health'] = 100
        super().__init__(enemy_data)
        self.speed = enemy_data.get('speed', 2.5)
        self.max_health = 100
        self.damage = enemy_data.get('damage', 8)

    def special_ability(self):
        return random.random() < 0.2

class Skeleton(Enemy):
    sprite_base_path = "client/assets/enemies/skeleton"
    def __init__(self, enemy_data):
        enemy_data['type'] = 'skeleton'
        enemy_data['max_health'] = 100
        super().__init__(enemy_data)
        self.speed = enemy_data.get('speed', 1.0)
        self.max_health = 100
        self.damage = enemy_data.get('damage', 12)
    
    def take_damage(self, damage):
        reduced_damage = damage * 0.8 if random.random() < 0.3 else damage
        super().take_damage(reduced_damage)

class Orc(Enemy):
    sprite_base_path = "client/assets/enemies/orc"
    def __init__(self, enemy_data):
        enemy_data['type'] = 'orc'
        enemy_data['max_health'] = 100
        super().__init__(enemy_data)
        self.speed = enemy_data.get('speed', 1.2)
        self.max_health = 100
        self.damage = enemy_data.get('damage', 15)
    
    def rage_mode(self):
        if self.health / self.max_health < 0.3:
            self.damage *= 1.5
            return True
        return False

def create_enemy(enemy_data):
    enemy_type_map = {
        "goblin": Goblin,
        "skeleton": Skeleton,
        "orc": Orc
    }
    
    enemy_class = enemy_type_map.get(enemy_data['type'], Enemy)
    return enemy_class(enemy_data)
