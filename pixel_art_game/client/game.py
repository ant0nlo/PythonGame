# client/game.py

import pygame
import socket
import threading
import json
import math
import time
import queue

from .map import Map
from .weapon import Weapon
from .item import create_item
from .enemy import create_enemy
from .hero import create_hero

HOST = '127.0.0.1'
PORT = 5555

class NetworkClient:
    def __init__(self, host, port, game, username, avatar, hero_class):
        self.host = host
        self.port = port
        self.game = game
        self.username = username
        self.avatar = avatar
        self.player_id = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.running = True
        self.message_queue = queue.Queue()
        threading.Thread(target=self.receive_loop, daemon=True).start()
        self.hero_class = hero_class
        self.send({"type": "join", "data": {"name": self.username, "avatar": self.avatar, "hero_class": self.hero_class}})

    def send(self, message):
        if not self.sock or self.sock.fileno() == -1:
            return
        try:
            self.sock.sendall((json.dumps(message) + "\n").encode())
        except (BrokenPipeError, OSError) as e:
            print("Connection closed:", e)
            self.close()

    def receive_loop(self):
        try:
            while self.running:
                data = self.sock.recv(4096)
                if not data:
                    break
                messages = data.decode().split('\n')
                for msg in messages:
                    if msg.strip():
                        self.message_queue.put(msg.strip())
        except (ConnectionResetError, TimeoutError) as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"Receive error: {e}")
        finally:
            self.close()

    def handle_message(self, message):
        message_type = message.get("type")
        data = message.get("data", {})

        if message_type == "health_update":
            player_id = data['player_id']
            new_health = data['health']
            update_source = data.get("source", "damage")
            
            if player_id == self.player_id and self.game.player:
                prev_health = self.game.player.health
                
                self.game.player.health = new_health    
                                
        if message_type == "update_state":
            self.game.update_state(data)

        elif message_type == "pickup_result": 
            if data.get("success"):
                item_type = message['data'].get('item_type')
                print(f"Successfully picked up {item_type}!")
                
                player = self.game.state['players'].get(self.player_id)
                if player:
                    from .item import create_item
                    item_data = {"type": item_type, "id": "", "x": 0, "y": 0, "value": 0.5}
                    item = create_item(item_data)
                    result = item.use(player)
                    print(f"Item use result: {result}")
                    print(f"Player health after use: {player.get('health')}")

        elif message_type == "join_ack":
            self.player_id = data.get("player_id")
            print(f"Received player ID: {self.player_id}")

        elif message_type == "special_result":
            success = data.get("success", False)   
            message_text = data.get("message", "")
            print(f"Special ability used: {message_text} (Success: {success})")

    def close(self):
        self.running = False
        self.send({"type": "leave", "data": {}})
        self.sock.close()

class Game:
    def __init__(self, username, avatar, hero_class):
        pygame.init()
        self.lock = threading.Lock()
        self.screen = pygame.display.set_mode((1100, 600))
        pygame.display.set_caption("2D Pixel Art Multiplayer Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = {"players": {}, "enemies": [], "items": []}
        self.username = username
        self.avatar = avatar
        self.hero_class = hero_class
        self.network = NetworkClient(HOST, PORT, self, self.username, self.avatar, self.hero_class)
        from .hero import create_hero
        self.player = create_hero(self.hero_class, 100, 100, self.username, self.avatar)
        self.map = Map()
        self.view_x = 0
        self.view_y = 0
        self.weapon = Weapon("sword")
        self.items = []
        self.enemies = []
        self.players = {}

        self.last_attack_time = 0
        self.attack_cooldown = 1.0  

        self.special_ability_cooldown = 3.0
        self.last_special_time = 0
        
    def process_network_messages(self):
        while not self.network.message_queue.empty():
            msg = self.network.message_queue.get()
            message = json.loads(msg)
            self.network.handle_message(message)
            
    def update_state(self, state):
        with self.lock:
            self.state["players"] = state.get("players", {})

            # Efficiently update enemies without recreating each frame
            enemy_dict = {enemy.id: enemy for enemy in self.enemies}
            updated_enemies = []

            for enemy_data in state.get("enemies", []):
                enemy_id = enemy_data["id"]
                if enemy_id in enemy_dict:
                    enemy = enemy_dict[enemy_id]
                    enemy.x = enemy_data["x"]
                    enemy.y = enemy_data["y"]
                    enemy.health = enemy_data["health"]
                    updated_enemies.append(enemy)
                else:
                    updated_enemies.append(create_enemy(enemy_data))

            self.enemies = updated_enemies

            # Efficiently update items
            item_dict = {item.id: item for item in self.items}
            updated_items = []

            for item_data in state.get("items", []):
                item_id = item_data["id"]
                if item_id in item_dict:
                    item = item_dict[item_id]
                    item.x = item_data["x"]
                    item.y = item_data["y"]
                    updated_items.append(item)
                else:
                    updated_items.append(create_item(item_data))

            self.items = updated_items
            
    def process_events(self):
        current_time = time.time()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.network.send({"type": "move", "data": {"direction": "up", "speed": 5}})
        if keys[pygame.K_DOWN]:
            self.network.send({"type": "move", "data": {"direction": "down", "speed": 5}})
        if keys[pygame.K_LEFT]:
            self.network.send({"type": "move", "data": {"direction": "left", "speed": 5}})
        if keys[pygame.K_RIGHT]:
            self.network.send({"type": "move", "data": {"direction": "right", "speed": 5}})

        for event in pygame.event.get():
            self.player.handle_event(event)

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_SPACE:
                    self.player.attack()
                    self.try_attack_enemy(current_time)

                elif event.key == pygame.K_q:
                    self.try_use_special_ability()

                elif event.key == pygame.K_e:
                    self.try_pickup_item()
                
    def update(self):
        dt = self.clock.get_time() / 1000.0  # Get delta time in seconds
        
        if self.network.player_id:
            player_data = self.state['players'].get(self.network.player_id)
            if player_data:
                self.player.update(player_data, dt)
        for enemy in self.enemies:
            enemy.update(dt)

    def update_viewport(self):
        SCREEN_WIDTH, SCREEN_HEIGHT = self.screen.get_size()
        player = self.state["players"].get(self.network.player_id)
        if player:
            # Calculate map boundaries in pixels
            map_pixel_width = self.map.width * self.map.tile_size
            map_pixel_height = self.map.height * self.map.tile_size
            
            # Center viewport on player, clamped to map boundaries
            target_x = player['x'] - SCREEN_WIDTH // 2
            target_y = player['y'] - SCREEN_HEIGHT // 2
            
            # Clamp to map edges
            self.view_x = max(0, min(target_x, map_pixel_width - SCREEN_WIDTH))
            self.view_y = max(0, min(target_y, map_pixel_height - SCREEN_HEIGHT))

    def render(self):
        self.screen.fill((0, 0, 0))
        self.update_viewport()

        # Draw map first 
        self.map.draw(self.screen, self.view_x, self.view_y)

        # Draw items
        for item in self.items:
            screen_x = item.x - self.view_x
            screen_y = item.y - self.view_y
            item.draw_at(self.screen, screen_x, screen_y)

        # Draw enemies
        for enemy in self.enemies:
            if enemy.health > 0:
                enemy.draw(self.screen, self.view_x, self.view_y)

        # Draw all players
        with self.lock:
            for player_id, info in self.state["players"].items():
                if info.get('state') == 'dead' and time.time() - info.get('death_time', 0) > 1:
                    continue
                if player_id not in self.players:
                    hero = create_hero(
                        info.get("hero_class", "warrior"),
                        info['x'],
                        info['y'],
                        info['name'],
                        info['avatar']
                    )
                    self.players[player_id] = hero
                else:
                    self.players[player_id].update(info, 1/60)

            for player_id, hero in self.players.items():
                player_data = self.state["players"].get(player_id)
                if player_data:
                    if player_data.get('state') == 'dead' and time.time() - player_data.get('death_time', 0) > 1:
                        continue
                    if player_data.get('state') != 'dead':
                        hero.x = player_data['x']
                        hero.y = player_data['y']
                    
                    hero.health = player_data['health']
                    hero.mana = player_data['mana']
                    
                    hero.draw(self.screen, self.view_x, self.view_y)

        self.render_hud()
        pygame.display.flip()
   
    def run(self):
        while self.running: 
            dt = self.clock.tick(60) / 1000.0
            self.process_network_messages() 
            self.process_events()
            self.update()
            self.render()
            self.clock.tick(60)
        self.network.close()
        pygame.quit()

    '''
    def handle_input(self):
        # Item pickup with specific keys
        keys = pygame.key.get_pressed()
        nearby = self.get_nearby_items()
        
        # General pickup with E
        if keys[pygame.K_e] and nearby:
            self.try_pickup_item()
            
        # Specific item pickup with E+1, E+2 etc
        if keys[pygame.K_e]:
            if keys[pygame.K_1] and len(nearby) > 0:
                self.network.send({
                    "type": "pickup",
                    "data": {"item_id": nearby[0].id}
                })
            elif keys[pygame.K_2] and len(nearby) > 1:
                self.network.send({
                    "type": "pickup", 
                    "data": {"item_id": nearby[1].id}
                })
            elif keys[pygame.K_3] and len(nearby) > 2:
                self.network.send({
                    "type": "pickup",
                    "data": {"item_id": nearby[2].id}
                })
    
    def try_drop_item(self, index):
        self.network.send({
            "type": "drop",
            "data": {"item_index": index}
        })
        
    '''

    def try_pickup_item(self):
        if not hasattr(self.network, 'player_id') or self.network.player_id is None:
            print("Cannot pickup - player ID not assigned yet")
            return
        
        nearby_items = self.get_nearby_items()
        if not nearby_items:
            print("No items nearby to pick up")
            return
        
        player = self.state['players'].get(self.network.player_id)
        if not player:
            print(f"Player {self.network.player_id} not found in game state")
            return
            
        closest_item = min(nearby_items, key=lambda item: 
            math.hypot(item.x - player['x'], item.y - player['y']))
        
        print(f"Attempting to pick up item: {closest_item.id} ({closest_item.type})")
        self.network.send({
            "type": "pickup",
            "data": {"item_id": closest_item.id}
        })

    def render_hud(self):
        font = pygame.font.SysFont(None, 24)
        weapon_text = f"Weapon: {self.weapon.type}"
        text = font.render(weapon_text, True, (255, 255, 255))
        self.screen.blit(text, (10, 10))

        player = self.state['players'].get(self.network.player_id)

        if player:
            bar_width = 200
            bar_height = 20
            padding = 10
            corner_radius = 5

            health_x = 10
            health_y = 10
            health_ratio = player['health'] / player['max_health']
            
            pygame.draw.rect(self.screen, (255, 0, 0), 
                            (health_x, health_y, bar_width, bar_height), 
                            border_radius=corner_radius)
            pygame.draw.rect(self.screen, (0, 255, 0), 
                            (health_x, health_y, bar_width * health_ratio, bar_height),
                            border_radius=corner_radius)

            mana_y = health_y + bar_height + padding
            mana_ratio = player['mana'] / player['max_mana']
            
            pygame.draw.rect(self.screen, (0, 0, 60), 
                            (health_x, mana_y, bar_width, bar_height), 
                            border_radius=corner_radius)
            pygame.draw.rect(self.screen, (0, 100, 255), 
                            (health_x, mana_y, bar_width * mana_ratio, bar_height),
                            border_radius=corner_radius)
            nearby = self.get_nearby_items()
            if nearby:
                text = font.render("Nearby items:", True, (255, 255, 255))
                self.screen.blit(text, (10, 60))
                
                for i, item in enumerate(nearby[:3]):
                    item_text = f"{i+1}. {item.type} ({item.value})"
                    text = font.render(item_text, True, (255, 255, 255))
                    self.screen.blit(text, (10, 85 + i*25))
                    
                    # Show key to press (E)
                    key_text = f"[E]"
                    text = font.render(key_text, True, (255, 255, 0))
                    self.screen.blit(text, (200, 85 + i*25))
            
            # Show inventory
            text = font.render("Inventory:", True, (255, 255, 255))
            self.screen.blit(text, (10, 160))
    
            for i, item in enumerate(player.get('inventory', [])):
                item_text = f"{i+1}. {item['type']}"
                text = font.render(item_text, True, (255, 255, 255))
                self.screen.blit(text, (10, 185 + i*25))

            print("Inventory Data:", player.get('inventory', []))
         
    def get_nearby_items(self):
        """Return items within pickup range of the player"""
        if not hasattr(self.network, 'player_id') or self.network.player_id is None:
            print("Player ID not yet assigned")
            return []
            
        player = self.state['players'].get(self.network.player_id)
        if not player:
            print(f"Player {self.network.player_id} not found in game state")
            return []
            
        nearby = []
        for item in self.items:
            distance = math.hypot(item.x - player['x'], item.y - player['y'])
            if distance < 50:  # Pickup radius
                nearby.append(item)
        return nearby
    
    def try_attack_enemy(self, current_time):
       # with self.lock:
        print("Attempting to attack enemy")
        print(f"Player ID: {self.network.player_id}")
        
        if not hasattr(self.network, 'player_id') or self.network.player_id is None:
            print("Cannot attack: No player ID assigned")
            return
        
        player = self.state['players'].get(self.network.player_id)
        if not player:
            print(f"Player {self.network.player_id} not found in game state")
            return
        
        print(f"Number of enemies: {len(self.enemies)}")
        
        print(f"Player position: x={player['x']}, y={player['y']}")
        for i, enemy in enumerate(self.enemies):
            print(f"Enemy {i} position: x={enemy.x}, y={enemy.y}")
        
        try:
            attack_result = self.weapon.attack(
                current_time, 
                player['x'], 
                player['y'], 
                self.enemies
            )
            
            if attack_result:
                print(f"Attack result: {attack_result}")
                self.network.send({
                    "type": "attack_enemy",
                    "data": {
                        "enemy_id": attack_result['enemy_id'],
                        "damage": attack_result['damage']
                    }
                })
                self.last_attack_time = current_time  
                self.player.attack()

            else:
                print("No enemy found to attack")
        except Exception as e:
            print(f"Error during attack attempt: {e}")
            import traceback
            traceback.print_exc()
    
    def try_use_special_ability(self):
        current_time = time.time()
        try:
            print("Attempting to use special ability")  
            if current_time - self.last_special_time < self.special_ability_cooldown:
                print("Special ability is on cooldown!")
                return

            if not hasattr(self.network, 'player_id') or self.network.player_id is None:
                print("Cannot use special - player ID not assigned yet")
                return

            player = self.state['players'].get(self.network.player_id)
            if not player:
                print("Player not found in state")
                return

            hero_class = player.get("hero_class")
            if not hero_class:
                print("Hero class missing from server state!")
                return

            ability_data = {}

            if hero_class == "mage":
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if not self.enemies:
                    print("No enemies in range.")
                    return

                closest_enemy = min(
                    self.enemies,
                    key=lambda e: math.hypot(e.x - mouse_x, e.y - mouse_y),
                    default=None
                )
                if closest_enemy:
                    ability_data = {
                        "type": "fireball",
                        "target_x": closest_enemy.x,
                        "target_y": closest_enemy.y,
                        "radius": 100,
                        "damage": 30
                    }
                else:
                    print("No enemies in range.")
                    return

            elif hero_class == "warrior":
                nearby_enemies = [
                    enemy.id for enemy in self.enemies
                    if math.hypot(enemy.x - player['x'], enemy.y - player['y']) <= 80
                ]
                ability_data = {
                    "type": "whirlwind",
                    "enemies": nearby_enemies,
                    "damage": 25
                }

            elif hero_class == "archer":
                if not self.enemies:
                    print("No enemies in range.")
                    return

                sorted_enemies = sorted(
                    self.enemies,
                    key=lambda e: math.hypot(e.x - player['x'], e.y - player['y'])
                )
                volley_targets = [enemy.id for enemy in sorted_enemies[:3] if math.hypot(enemy.x - player['x'], enemy.y - player['y']) <= 200]

                ability_data = {
                    "type": "volley",
                    "enemies": volley_targets,
                    "damage": 15
                }

            else:
                print(f"Unknown hero class: {hero_class}")
                return

            if ability_data:
                print(f"Sending special ability: {ability_data}")
                self.network.send({
                    "type": "use_special",
                    "data": ability_data
                })
                self.last_special_time = current_time

        except Exception as e:
            print(f"Error in try_use_special_ability: {e}")
            import traceback
            traceback.print_exc()