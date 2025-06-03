import pygame
import math
import time
from .weapon import Weapon
from .animation import Animation

_animation_cache = {}

class Hero:
    """Base hero class that all specific hero types will inherit from"""
    def __init__(self, x, y, username="", avatar=""):
        self.x = x
        self.y = y
        self.username = username
        self.avatar = avatar
        self.inventory = []
        self.health = 100
        self.max_health = 100
        self.mana = 100
        self.max_mana = 100
        self.base_speed = 5
        self.defense = 0
        self.special_cooldown = 10.0  
        self.last_special_use = 0
        self.state = "idle"
        self.primary_color = (0, 255, 0)

        rect_width = 64
        rect_height = 64
        self.rect = pygame.Rect(x - (rect_width // 2), y - (rect_height // 2), rect_width, rect_height)
        
        self.weapon = None

        # Animation and state tracking
        self.is_moving = False
        self.is_attacking = False
        self.is_dead = False
        self.prev_x = x 
        self.prev_y = y

        # Animation timings
        self.attack_start_time = 0
        self.attack_animation_duration = 0.5 
        self.last_hit_time = 0


        # default sprite path
        if not hasattr(self, 'sprite_base_path'):
            self.sprite_base_path = "client/assets/enemies/goblin"
        
        self._init_animations()
        
    def _init_animations(self):
        """Initialize animations with caching"""
        anim_paths = {
            "idle": f"{self.sprite_base_path}/idle.png",
            "run": f"{self.sprite_base_path}/run.png",
            "attack": f"{self.sprite_base_path}/attack.png",
            "death": f"{self.sprite_base_path}/death.png" 
        }
        
        animation_specs = {
            "idle": (4, 0.2),
            "run": (8, 0.05),
            "attack": (8, 0.05),
            "death": (4, 0.15)
        }
        
        self.animations = {}
        for state, path in anim_paths.items():
            sprite_sheet = _animation_cache.get(path)
            if sprite_sheet is None:
                try:
                    sprite_sheet = pygame.image.load(path).convert_alpha()
                    _animation_cache[path] = sprite_sheet
                    print(f"Successfully loaded {path}")
                except Exception as e:
                    print(f"Failed to load {path}: {e}")
                    if hasattr(self, 'create_fallback'):
                        sprite_sheet = self.create_fallback(state)
                        print(f"Created fallback surface for {path}")
                    else:
                        continue
                    
            frames, duration = animation_specs[state]
            self.animations[state] = Animation(sprite_sheet, 150, 150, frames, duration)
        
    def add_item(self, item):
        self.inventory.append(item)
        
    def remove_item(self, item):
        if item in self.inventory:
            self.inventory.remove(item)
    
    def draw(self, screen, view_x=0, view_y=0):
        """Draw the hero with health and mana bars"""
        current_frame = self.animations[self.state].get_frame()
        screen_x = self.x - view_x
        screen_y = self.y - view_y
        
        frame_width = current_frame.get_width()
        frame_height = current_frame.get_height()
        
        centered_x = screen_x - (frame_width // 2)
        centered_y = screen_y - (frame_height // 2)
        
        screen.blit(current_frame, (centered_x, centered_y))
               
    def use_special_ability(self, current_time, enemies=None):
        """Base method for special ability - to be overridden by subclasses"""
        if current_time - self.last_special_use < self.special_cooldown:
            return {"success": False, "message": "Ability on cooldown"}
        
        mana_cost = 25
        if self.mana < mana_cost:
            return {"success": False, "message": "Not enough mana"}
            
        self.mana -= mana_cost
        self.last_special_use = current_time
        
        return {"success": True, "message": "Used special ability"}
    
    def update(self, player_data, dt):
        health = player_data.get('health')
        if health is not None:
            self.health = health
        mana = player_data.get('mana')
        if mana is not None:
            self.mana = mana

        self._detect_movement(player_data)
        self._update_attack_state()
        self._update_death_state()

        if self.is_dead:
            self.state = "death"
        elif self.is_attacking:
            self.state = "attack"
        elif self.is_moving:
            self.state = "run"
        else:
            self.state = "idle"

        if self.state in self.animations:
            self.animations[self.state].update(dt)

    def _detect_movement(self, player_data):
        """Check if player has moved since last update"""
        new_x = player_data.get('x', self.x)
        new_y = player_data.get('y', self.y)
        
        self.rect.center = (new_x, new_y)
        self.is_moving = (new_x != self.prev_x) or (new_y != self.prev_y)
        
        self.x = new_x
        self.y = new_y
        self.prev_x = new_x
        self.prev_y = new_y
        
        rect_width = self.rect.width
        rect_height = self.rect.height
        self.rect.x = new_x - (rect_width // 2)
        self.rect.y = new_y - (rect_height // 2)

    def _update_attack_state(self):
        """Handle attack animation timing"""
        if self.is_attacking:
            elapsed = time.time() - self.attack_start_time
            if elapsed >= self.attack_animation_duration:
                self.is_attacking = False

    def _update_death_state(self):
        """Update death state"""
        self.is_dead = self.health <= 0

    def attack(self):
        if not self.is_attacking and not self.is_dead:
            self.is_attacking = True
            self.attack_start_time = time.time()
            if "attack" in self.animations:
                self.animations["attack"].current_frame = 0
                self.animations["attack"].last_update = 0 

    def handle_event(self, event):
        """Handle animation-related events"""
        if event.type == pygame.USEREVENT + 1:
            self.was_hit = False
    
class Warrior(Hero):
    """Tank class with high health and melee damage"""
    def __init__(self, x, y, username="", avatar=""):
        self.sprite_base_path = "client/assets/enemies/goblin"
        super().__init__(x, y, username, avatar)
        self.max_health = 150
        self.health = 150
        self.max_mana = 80
        self.mana = 80
        self.base_speed = 4
        self.defense = 20
        self.primary_color = (180, 0, 0) 
        self.weapon = Weapon("axe")
        self.special_cooldown = 15.0
    
    def use_special_ability(self, current_time, enemies=None):
        """Warrior's Whirlwind Attack - damages all enemies in range"""
        result = super().use_special_ability(current_time, enemies)
        if not result["success"]:
            return result
            
        whirlwind_range = 80
        affected_enemies = []
        
        if enemies:
            for enemy in enemies:
                distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
                if distance <= whirlwind_range:
                    affected_enemies.append(enemy.id)
        
        return {
            "success": True,
            "type": "whirlwind",
            "enemies": affected_enemies,
            "damage": 25,
            "message": f"Whirlwind Attack hit {len(affected_enemies)} enemies"
        }

class Archer(Hero):
    """Range attacker with high speed and precision"""
    sprite_base_path = "client/assets/enemies/skeleton"
    
    def __init__(self, x, y, username="", avatar=""):
        super().__init__(x, y, username, avatar)
        self.max_health = 90
        self.health = 90
        self.max_mana = 100
        self.mana = 100
        self.base_speed = 6
        self.defense = 8
        self.primary_color = (0, 150, 0)  
        self.weapon = Weapon("bow")
        self.special_cooldown = 12.0
    
    def create_fallback(self, state):
        """Create a fallback surface for failed image loads"""
        if state == "idle" or state == "take_hit" or state == "death":
            return pygame.Surface((150*4, 150), pygame.SRCALPHA)
        else:
            return pygame.Surface((150*8, 150), pygame.SRCALPHA)
 
    def use_special_ability(self, current_time, enemies=None):
        """Archer's Volley - shoots multiple arrows at the nearest 3 enemies"""
        result = super().use_special_ability(current_time, enemies)
        if not result["success"]:
            return result
            
        max_targets = 3
        volley_range = 200
        targets = []
        
        if enemies:
            sorted_enemies = sorted(
                enemies, 
                key=lambda e: math.hypot(e.x - self.x, e.y - self.y)
            )
            
            for enemy in sorted_enemies[:max_targets]:
                distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
                if distance <= volley_range:
                    targets.append(enemy.id)
        
        return {
            "success": True,
            "type": "volley",
            "enemies": targets,
            "damage": 15,
            "message": f"Arrow Volley targeted {len(targets)} enemies"
        }

class Mage(Hero):
    """Magic user with high mana"""
    sprite_base_path = "client/assets/characters/mage"
    
    def __init__(self, x, y, username="", avatar=""):
        super().__init__(x, y, username, avatar)
        self.max_health = 80
        self.health = 80
        self.max_mana = 150
        self.mana = 150
        self.base_speed = 4
        self.defense = 5
        self.primary_color = (100, 100, 255)
        self.weapon = Weapon("staff")
        self.special_cooldown = 8.0
    
    def use_special_ability(self, current_time, enemies=None):
        """Mage's Fireball - area damage around a target location"""
        result = super().use_special_ability(current_time, enemies)
        if not result["success"]:
            return result
            
        fireball_range = 100
        best_target = None
        max_affected = 0
        
        if enemies and len(enemies) > 0:
            for center_enemy in enemies:
                affected = 0
                for other in enemies:
                    distance = math.hypot(
                        other.x - center_enemy.x, 
                        other.y - center_enemy.y
                    )
                    if distance <= fireball_range:
                        affected += 1
                
                if affected > max_affected:
                    max_affected = affected
                    best_target = center_enemy
        
        if best_target:
            return {
                "success": True,
                "type": "fireball",
                "target_x": best_target.x,
                "target_y": best_target.y,
                "radius": fireball_range,
                "damage": 30,
                "message": f"Fireball cast at ({best_target.x}, {best_target.y})"
            }
        
        return {
            "success": False,
            "message": "No suitable target found for Fireball"
        }


def create_hero(hero_class, x=100, y=100, username="", avatar=""):
    """Factory method to create heroes by class name"""
    hero_classes = {
        "warrior": Warrior,
        "archer": Archer,
        "mage": Mage,
    }
    
    hero_constructor = hero_classes.get(hero_class.lower(), Hero)
    return hero_constructor(x, y, username, avatar)