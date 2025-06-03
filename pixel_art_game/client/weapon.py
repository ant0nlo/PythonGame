# client/weapon.py

import pygame
import math
import time

class Weapon:
    def __init__(self, weapon_type):
        self.type = weapon_type
        
        self.stats = {
            # Warrior weapons
            "sword": {"damage": 20, "range": 50, "speed": 0.8, "effect": "bleed"},
            "axe": {"damage": 25, "range": 40, "speed": 0.6, "effect": "stun"},
            
            # Archer weapons
            "bow": {"damage": 12, "range": 180, "speed": 1.0, "effect": "slow"},
            "crossbow": {"damage": 18, "range": 150, "speed": 0.7, "effect": "pierce"},
            
            # Mage weapons
            "staff": {"damage": 10, "range": 120, "speed": 1.2, "effect": "burn"},
            "wand": {"damage": 8, "range": 100, "speed": 1.5, "effect": "freeze"},
            
            # Default 
            "default": {"damage": 10, "range": 40, "speed": 1.0, "effect": None}
        }.get(weapon_type, {"damage": 10, "range": 40, "speed": 1.0, "effect": None})
        
        self.damage = self.stats["damage"]
        self.range = self.stats["range"]
        self.attack_speed = self.stats["speed"]
        self.effect = self.stats["effect"]
        
        self.attack_cooldown = 1.0 / self.attack_speed
        self.last_attack = 0
        
    def can_attack(self, current_time):
        """Check if weapon cooldown has passed"""
        return current_time - self.last_attack >= self.attack_cooldown

    def find_target_enemy(self, player_x, player_y, enemies):
        """Find the closest enemy within attack range"""
        closest_enemy = None
        min_distance = float('inf')
        
        for enemy in enemies:
            distance = math.hypot(enemy.x - player_x + 30, enemy.y - player_y + 80)
            
            if distance <= self.range and distance < min_distance:
                closest_enemy = enemy
                min_distance = distance
        
        return closest_enemy

    def attack(self, current_time, player_x, player_y, enemies):
        """Attempt to attack the closest enemy"""
        if not self.can_attack(current_time):
            return None

        target = self.find_target_enemy(player_x, player_y, enemies)
        if target:
            self.last_attack = current_time
            attack_data = {
                "enemy_id": target.id,
                "damage": self.damage
            }
            
            # special effect
            if self.effect:
                attack_data["effect"] = self.effect
                
            return attack_data
        
        return None
        
