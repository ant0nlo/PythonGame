'''
# client/effects.py

import time
import pygame

class Effect:
    """Base class for all status effects"""
    def __init__(self, duration=3.0, strength=1.0):
        self.duration = duration  # Effect duration in seconds
        self.start_time = time.time()
        self.strength = strength  # Multiplier for effect power
        
    def is_active(self, current_time):
        """Check if effect is still active"""
        return (current_time - self.start_time) < self.duration
    
    def get_remaining_time(self, current_time):
        """Get remaining effect time in seconds"""
        return max(0, self.duration - (current_time - self.start_time))
    
    def apply(self, target):
        """Apply effect to target - to be overridden"""
        pass
    
    def remove(self, target):
        """Remove effect from target - to be overridden"""
        pass


class DamageOverTime(Effect):
    """Effect that deals damage periodically (bleed, burn, poison)"""
    def __init__(self, effect_type, damage_per_tick=5, tick_rate=1.0, duration=3.0, strength=1.0):
        super().__init__(duration, strength)
        self.effect_type = effect_type
        self.damage_per_tick = damage_per_tick * strength
        self.tick_rate = tick_rate  # How many seconds between ticks
        self.last_tick = self.start_time
        self.color = self.get_effect_color()
    
    def get_effect_color(self):
        """Return color based on effect type"""
        colors = {
            "bleed": (255, 0, 0),      # Red
            "burn": (255, 165, 0),     # Orange
            "poison": (0, 255, 0)      # Green
        }
        return colors.get(self.effect_type, (255, 255, 255))
    
    def update(self, current_time, target):
        """Apply periodic damage if it's time for a tick"""
        if not self.is_active(current_time):
            return 0
            
        if (current_time - self.last_tick) >= self.tick_rate:
            self.last_tick = current_time
            # Return damage dealt this tick
            return self.damage_per_tick
            
        return 0
    
    def draw(self, screen, target_x, target_y):
        """Visualize the effect on target"""
        # Create particle effect around target
        for i in range(3):
            # Random offset within 15 pixels
            offset_x = pygame.math.Vector2(1, 0).rotate(i * 120).x * 15
            offset_y = pygame.math.Vector2(1, 0).rotate(i * 120).y * 15
            
            # Draw colored circle with alpha
            pygame.draw.circle(
                screen, 
                (*self.color, 150),  # Color with alpha
                (target_x + offset_x, target_y + offset_y), 
                5
            )


class MovementEffect(Effect):
    """Effect that modifies movement (slow, stun, speed)"""
    def __init__(self, effect_type, modifier=0.5, duration=2.0, strength=1.0):
        super().__init__(duration, strength)
        self.effect_type = effect_type
        
        # Calculate modifier based on effect type and strength
        if effect_type == "slow":
            # Slow reduces speed (0.5 = 50% normal speed)
            self.modifier = 1.0 - (modifier * strength)
        elif effect_type == "stun":
            # Stun sets speed to 0
            self.modifier = 0.0
        elif effect_type == "speed":
            # Speed increases speed (1.5 = 150% normal speed)
            self.modifier = 1.0 + (modifier * strength)
        else:
            self.modifier = 1.0
    
    def apply(self, target):
        """Apply movement modification"""
        # Store original speed if not already stored
        if not hasattr(target, "original_speed"):
            target.original_speed = target.speed
        
        # Apply modifier
        if self.effect_type == "stun":
            target.speed = 0
        else:
            target.speed = target.original_speed * self.modifier
    
    def remove(self, target):
        """Restore original speed"""
        if hasattr(target, "original_speed"):
            target.speed = target.original_speed


class DefenseEffect(Effect):
    """Effect that modifies defense (vulnerability, resistance)"""
    def __init__(self, effect_type, modifier=0.5, duration=5.0, strength=1.0):
        super().__init__(duration, strength)
        self.effect_type = effect_type
        
        # Calculate modifier based on effect type and strength
        if effect_type == "vulnerability":
            # Vulnerability increases damage taken
            self.modifier = 1.0 + (modifier * strength)
        elif effect_type == "resistance":
            # Resistance reduces damage taken
            self.modifier = 1.0 - (modifier * strength)
        else:
            self.modifier = 1.0
    
    def apply(self, target):
        """Apply defense modification"""
        # Store original defense if not already stored
        if not hasattr(target, "original_defense"):
            target.original_defense = getattr(target, "defense", 0)
            
        # Apply modifier to defense value
        target.defense_multiplier = self.modifier
    
    def remove(self, target):
        """Restore original defense"""
        if hasattr(target, "original_defense"):
            target.defense = target.original_defense
        target.defense_multiplier = 1.0


class FireballEffect:
    def __init__(self, x, y):
        self.particles = [
            {"pos": (x, y), "color": (255, 69, 0), "radius": 0}
        ]
    
    def update(self):
        for p in self.particles:
            p["radius"] += 2
            if p["radius"] > 100:
                self.particles.remove(p)
    
    def draw(self, screen):
        for p in self.particles:
            pygame.draw.circle(
                screen,
                (*p["color"], 100),  # Semi-transparent
                p["pos"],
                p["radius"],
                2
            )

class EffectManager:
    """Manages active effects on entities"""
    def __init__(self):
        self.effects = {}  # Dict of entity_id -> list of active effects
    
    def add_effect(self, entity_id, effect):
        """Add a new effect to an entity"""
        if entity_id not in self.effects:
            self.effects[entity_id] = []
            
        # Add the effect
        self.effects[entity_id].append(effect)
        return True
    
    def update_effects(self, current_time):
        """Update all active effects and remove expired ones"""
        expired_effects = []
        
        for entity_id, effect_list in self.effects.items():
            # Filter out expired effects
            active_effects = []
            for effect in effect_list:
                if effect.is_active(current_time):
                    active_effects.append(effect)
                else:
                    expired_effects.append((entity_id, effect))
            
            # Update the list with only active effects
            self.effects[entity_id] = active_effects
        
        # Return list of expired effects for cleanup
        return expired_effects
    
    def get_entity_effects(self, entity_id):
        """Get all active effects for an entity"""
        return self.effects.get(entity_id, [])
    
    def clear_entity_effects(self, entity_id):
        """Remove all effects from an entity"""
        if entity_id in self.effects:
            del self.effects[entity_id]
    
    def draw_effects(self, screen, entities):
        """Draw visual indicators for active effects"""
        current_time = time.time()
        
        for entity_id, effect_list in self.effects.items():
            # Find entity position
            entity = next((e for e in entities if getattr(e, "id", None) == entity_id), None)
            if not entity:
                continue
                
            # Draw each effect
            for effect in effect_list:
                if hasattr(effect, "draw") and effect.is_active(current_time):
                    effect.draw(screen, entity.x, entity.y)
'''