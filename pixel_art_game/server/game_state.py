import threading
import math
import time
import random
import json

from .config import hardcoded_layout

class GameState:
    def __init__(self):
        self.players = {}
        self.enemies = []
        self.items = []
        self.lock = threading.RLock()
        self.next_item_id = 1
        self.next_enemy_id = 1
        self.player_attacks = {}
        self.tile_size = 64
        self.width = len(hardcoded_layout[0])
        self.height = len(hardcoded_layout)
        impassable_tile_ids = {4, 5, 6, 7, 8, 9, 10, 11}
        self.map = [
            [{'passable': tile not in impassable_tile_ids} for tile in row]
            for row in hardcoded_layout
        ]

        with self.lock:
            self._initialize_enemies()
            self._initialize_items()

    def _initialize_enemies(self):
        """Create initial enemy spawns in passable positions, centered on tiles"""
        enemy_types = ["goblin", "skeleton", "orc"]
        for _ in range(8):
            placed = False
            attempts = 0
            max_attempts = 100  # Prevent infinite loops
            
            while not placed and attempts < max_attempts:
                tile_x = random.randint(0, self.width - 1)
                tile_y = random.randint(0, self.height - 1)
                
                x = tile_x * self.tile_size + self.tile_size // 2
                y = tile_y * self.tile_size + self.tile_size // 2
                
                if (self.is_passable(x, y) and 
                    self.is_passable(x + 32, y) and 
                    self.is_passable(x, y + 32) and
                    math.hypot(x - 100, y - 100) > 200):
                    
                    self.enemies.append({
                        "id": f"enemy_{self.next_enemy_id}",
                        "type": random.choice(enemy_types),
                        "x": x,
                        "y": y,
                        "speed": random.uniform(1.0, 2.5),
                        "health": 100,
                        "damage": random.randint(5, 15),
                        "last_hit_time": 0
                    })
                    self.next_enemy_id += 1
                    placed = True
                    
                attempts += 1

    def _initialize_items(self):
        """Create initial item spawns in passable positions"""
        item_types = ["sword", "shield", "potion", "coin", "mana_potion"]
        for _ in range(11):
            placed = False
            attempts = 0
            max_attempts = 100
            
            while not placed and attempts < max_attempts:
                x = random.randint(50, (self.width - 1) * self.tile_size - 50)
                y = random.randint(50, (self.height - 1) * self.tile_size - 50)
                
                if (self.is_passable(x, y) and 
                    self.is_passable(x + 24, y) and 
                    self.is_passable(x, y + 24)):
                    
                    self.items.append({
                        "id": f"item_{self.next_item_id}",
                        "type": random.choice(item_types),
                        "x": x,
                        "y": y,
                        "value": round(random.uniform(0.1, 1.0), 1)
                    })
                    self.next_item_id += 1
                    placed = True
                    
                attempts += 1

    def add_player(self, player_id, name, avatar, hero_class="warrior"):
        with self.lock:
            base_stats = {
                "name": name,
                "avatar": avatar,
                "x": 100,
                "y": 100,
                "inventory": [],
                "health": 100,
                "max_health": 100,
                "mana": 100,
                "max_mana": 100,
                "defense": 0,
                "hero_class": hero_class,
                "effects": []
            }
            
            if hero_class == "warrior":
                base_stats.update({
                    "health": 150,
                    "max_health": 150,
                    "mana": 80,
                    "max_mana": 80,
                    "defense": 20,
                    "weapon": "axe"
                })
            elif hero_class == "archer":
                base_stats.update({
                    "health": 90,
                    "max_health": 90,
                    "mana": 100,
                    "max_mana": 100,
                    "defense": 8,
                    "weapon": "bow"
                })
            elif hero_class == "mage":
                base_stats.update({
                    "health": 80,
                    "max_health": 80,
                    "mana": 150,
                    "max_mana": 150,
                    "defense": 5,
                    "weapon": "staff"
                })
            
            self.players[player_id] = base_stats

    def is_passable(self, x, y):
        """Check if a position is passable (in pixel coordinates)"""
        tile_x = int(x // self.tile_size)
        tile_y = int(y // self.tile_size)
        
        if not (0 <= tile_x < self.width and 0 <= tile_y < self.height):
            return False
            
        return self.map[tile_y][tile_x]['passable']
    
    def move_player(self, player_id, dx, dy):
        with self.lock:
            player = self.players.get(player_id)
            if player:
                new_x = player["x"] + dx
                new_y = player["y"] + dy
                
                if self.is_passable(new_x, new_y) and self.is_passable(new_x + 32, new_y) and self.is_passable(new_x, new_y + 32):
                    player["x"] = new_x
                    player["y"] = new_y

    def remove_player(self, player_id):
        with self.lock:
            self.players.pop(player_id, None)

    def pickup_item(self, player_id, item_id):
        with self.lock:
            player = self.players.get(player_id)
            if not player:
                return False
            for i, item in enumerate(self.items):
                if item['id'] == item_id:
                    distance = math.hypot(player['x'] - item['x'], player['y'] - item['y'])
                    if distance <= 50:
                        player['inventory'].append(item)
                        del self.items[i]
                        return True
                    return False
            return False

    def get_picked_item_type(self, player_id, item_id):
        with self.lock:
            player = self.players.get(player_id)
            if player:
                for item in player['inventory']:
                    if item['id'] == item_id:
                        return item['type']
            return None

    def drop_item(self, player_id, item_index):
        with self.lock:
            player = self.players.get(player_id)
            if not player:
                return False
            if item_index < 0 or item_index >= len(player['inventory']):
                return False
            item = player['inventory'].pop(item_index)
            item['x'] = player['x']
            item['y'] = player['y']
            self.items.append(item)
            return True

    def get_state(self):
        with self.lock:
            return {
                "players": {
                    pid: {
                        "name": p["name"],
                        "avatar": p["avatar"],
                        "x": p["x"],
                        "y": p["y"],
                        "inventory": p["inventory"],
                        "health": p["health"],
                        "max_health": p["max_health"],  
                        "mana": p["mana"], 
                        "max_mana": p["max_mana"],  
                        "hero_class": p["hero_class"]  
                    } for pid, p in self.players.items()
                },
                "enemies": self.enemies,
                "items": self.items
            }

    def update_effects(self):
        """Update all active effects and remove dead players"""
        with self.lock:
            current_time = time.time()
            dead_players = [
                pid for pid, p in self.players.items()
                if p.get('state') == 'dead' and (current_time - p.get('death_time', 0)) > 1.0
            ]

            for pid in dead_players:
                del self.players[pid]

    def handle_enemy_attack(self, player_id, enemy_id, damage, effect=None):
        with self.lock:

            for i, enemy in enumerate(self.enemies):
                if enemy['id'] == enemy_id:
                    if effect:
                        self.apply_effect(enemy_id, {
                            "type": effect,
                            "duration": 3.0,
                            "strength": 1.0
                        })
                    # Reduce enemy health
                    enemy['health'] = enemy.get('health', 100) - damage
                    
                    if enemy['health'] <= 0:
                        self.enemies.pop(i)
                        if random.random() < 0.3:
                            self.generate_item(x=enemy['x'], y=enemy['y'])
                    
                    return True
            return False
        
    def update_enemies(self):
        with self.lock:
            if not self.players:
                return
                
            ACTIVATION_RADIUS = 300
            AGGRO_RANGE = 200
            ATTACK_DISTANCE = 64
            CHASE_SPEED_MULTIPLIER = 1.5
            current_time = time.time()
            
            for enemy in self.enemies:
                alive_players = [
                (pid, p) for pid, p in self.players.items() 
                if p.get('state') != 'dead'
                ]
                
                if not alive_players:
                    continue

                nearest_player_id, nearest_player = min(
                    ((pid, p) for pid, p in self.players.items()),
                    key=lambda item: math.hypot(item[1]['x'] - enemy['x'], item[1]['y'] - enemy['y'])
                )
                
                target_x = nearest_player['x'] - 30  # 20 blocks west
                target_y = nearest_player['y'] - 80  # 60 blocks north
                
                dx = target_x - enemy['x']
                dy = target_y - enemy['y']
                distance = math.hypot(dx, dy)

                if distance > ACTIVATION_RADIUS:
                    continue 

                if not self.has_line_of_sight(enemy['x'], enemy['y'], nearest_player['x'], nearest_player['y']):
                    continue  # Enemy can't see player, won't chase

                if distance <= AGGRO_RANGE and distance > 0:
                    move_speed = enemy.get('speed', 2) * CHASE_SPEED_MULTIPLIER
                    move_factor = move_speed / distance
                    new_x = enemy['x'] + dx * move_factor
                    new_y = enemy['y'] + dy * move_factor

                    enemy_width = 32
                    enemy_height = 32
                    if (self.is_passable(new_x, new_y) and 
                        self.is_passable(new_x + enemy_width, new_y) and 
                        self.is_passable(new_x, new_y + enemy_height) and
                        self.is_passable(new_x + enemy_width, new_y + enemy_height)):
                        enemy['x'] = new_x
                        enemy['y'] = new_y
                        
                if distance < ATTACK_DISTANCE:
                    if current_time - enemy.get('last_hit_time', 0) > 1.0:
                        enemy['last_hit_time'] = current_time
                        print(f"Enemy attacking offset position at {target_x},{target_y}")
                        
                        nearest_player['health'] -= enemy.get('damage', 10)
                        
                        if nearest_player['health'] <= 0:
                            from .network import broadcast
                            broadcast(json.dumps({
                                "type": "player_death",
                                "data": {"player_id": nearest_player_id}
                            }))
                            del self.players[nearest_player_id]
                            
    def generate_item(self, item_type=None, x=None, y=None):
        with self.lock:
            item_types = ["sword", "shield", "potion", "coin"]
            item = {
                "id": f"item_{self.next_item_id}",
                "type": item_type or random.choice(item_types),
                "x": x if x is not None else random.randint(50, 750),
                "y": y if y is not None else random.randint(50, 550),
                "value": round(random.uniform(0.1, 1.0), 1)
            }
            self.items.append(item)
            self.next_item_id += 1
            return item
    
    def heal_player(self, player_id, heal_amount):
        with self.lock:
            player = self.players.get(player_id)
            if player:
                current_health = player.get('health', 100)
                max_health = player.get('max_health', 100)
                new_health = min(max_health, current_health + heal_amount)
                player['health'] = new_health
                return new_health
        return None

    def use_special_ability(self, player_id, ability_data):
        with self.lock:
            player = self.players.get(player_id)
            if not player:
                return {"success": False, "message": "Player not found"}
            
            # Get ability type from the data
            ability_type = ability_data.get("type")
            if not ability_type:
                return {"success": False, "message": "No ability type specified"}
                
            mana_cost = 25 
            if player["mana"] < mana_cost:
                return {"success": False, "message": "Not enough mana"}
                
            player["mana"] -= mana_cost
            
            if ability_type == "whirlwind":
                affected_enemies = ability_data.get("enemies", [])
                damage = ability_data.get("damage", 20)
                
                for enemy_id in affected_enemies:
                    self.handle_enemy_attack(player_id, enemy_id, damage)
                    
                return {
                    "success": True, 
                    "message": f"Whirlwind hit {len(affected_enemies)} enemies"
                }
                
            elif ability_type == "volley":
                targets = ability_data.get("enemies", [])
                damage = ability_data.get("damage", 15)
                
                for enemy_id in targets:
                    self.handle_enemy_attack(player_id, enemy_id, damage)
                    
                return {
                    "success": True,
                    "message": f"Volley hit {len(targets)} targets"
                }
                
            elif ability_type == "fireball":
                target_x = ability_data.get("target_x", 0)
                target_y = ability_data.get("target_y", 0)
                radius = ability_data.get("radius", 100)
                damage = ability_data.get("damage", 30)

                print(f"Fireball used at ({target_x}, {target_y}) with radius {radius} and damage {damage}")

                affected = []
                for enemy in self.enemies:
                    distance = math.hypot(enemy["x"] - target_x, enemy["y"] - target_y)
                    if distance <= radius:
                        affected.append(enemy["id"])
                        distance_factor = 1 - (distance / radius)
                        actual_damage = int(damage * distance_factor)
                        print(f"Enemy {enemy['id']} at ({enemy['x']}, {enemy['y']}) took {actual_damage} damage.")
                        self.handle_enemy_attack(player_id, enemy["id"], actual_damage)

                print(f"Total enemies hit: {len(affected)}")

                return {
                    "success": True,
                    "message": f"Fireball hit {len(affected)} enemies"
                }
            
            return {"success": False, "message": "Unknown ability type"}

    def apply_effect(self, target_id, effect_data):
        """Apply a status effect to a player or enemy"""
        with self.lock:
            effect_type = effect_data.get("type")
            duration = effect_data.get("duration", 3.0)
            strength = effect_data.get("strength", 1.0)
            current_time = time.time()
            new_effect = {
                "type": effect_type,
                "duration": duration,
                "strength": strength,
                "start_time": current_time
            }
            
            if target_id in self.players:
                target = self.players[target_id]
                if "effects" not in target:
                    target["effects"] = []
                    
                target["effects"].append(new_effect)
                return True
                
            for enemy in self.enemies:
                if enemy["id"] == target_id:
                    if "effects" not in enemy:
                        enemy["effects"] = []
                        
                    enemy["effects"].append(new_effect)
                    return True
            
            return False

    def add_mana(self, player_id, mana_amount):
        with self.lock:
            player = self.players.get(player_id)
            if player:
                current_mana = player.get('mana', 100)
                max_mana = player.get('max_mana', 100)
                new_mana = min(max_mana, current_mana + mana_amount)
                player['mana'] = new_mana
                return new_mana
        return None
    
    def has_line_of_sight(self, x0, y0, x1, y1):
        """Bresenham's line algorithm to check if there's a wall between two points"""
        tile_x0, tile_y0 = int(x0 // self.tile_size), int(y0 // self.tile_size)
        tile_x1, tile_y1 = int(x1 // self.tile_size), int(y1 // self.tile_size)

        dx = abs(tile_x1 - tile_x0)
        dy = abs(tile_y1 - tile_y0)
        sx = 1 if tile_x0 < tile_x1 else -1
        sy = 1 if tile_y0 < tile_y1 else -1
        err = dx - dy

        while tile_x0 != tile_x1 or tile_y0 != tile_y1:
            if not (0 <= tile_x0 < self.width and 0 <= tile_y0 < self.height) or not self.map[tile_y0][tile_x0]['passable']:
                return False
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                tile_x0 += sx
            if e2 < dx:
                err += dx
                tile_y0 += sy

        return True

game_state = GameState()