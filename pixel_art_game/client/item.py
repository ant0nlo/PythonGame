# client/item.py

import pygame
import random

class Item:
    def __init__(self, item_data):
        self.id = item_data['id']
        self.type = item_data['type']
        self.x = item_data['x']
        self.y = item_data['y']
        self.value = item_data.get('value', 0.5)
        self.image = pygame.Surface((24, 24))
        
    def use(self, player):
        """Base use method to be overridden by specific item types"""
        pass
    
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def draw_at(self, screen, screen_x, screen_y):
        screen.blit(self.image, (screen_x, screen_y))

class HealPotion(Item):
    def __init__(self, item_data):
        super().__init__(item_data)
        self.image = pygame.transform.scale(
    pygame.image.load("client/assets/items/potion.png").convert_alpha(),
    (24, 24)
)
        self.heal_amount = int(self.value * 50)
    
    def use(self, player):
            """Trigger healing through network"""
            from .game import NetworkClient
            
            # Find the NetworkClient instance to send message
            import inspect
            for frame_record in inspect.stack():
                frame = frame_record.frame
                if 'self' in frame.f_locals:
                    obj = frame.f_locals['self']
                    if isinstance(obj, NetworkClient):
                        obj.send({
                            "type": "use_item", 
                            "data": {
                                "item_type": "potion", 
                                "heal_amount": self.heal_amount
                            }
                        })
                        break
            
            return f"Attempting to heal for {self.heal_amount} health points"

class Shield(Item):
    def __init__(self, item_data):
        super().__init__(item_data)
        self.image = pygame.transform.scale(
            pygame.image.load("client/assets/items/shield.png").convert_alpha(),
            (24, 24))
        self.defense_bonus = self.value * 10
    
    def use(self, player):
        """Add temporary defense bonus"""
        player['defense_bonus'] = self.defense_bonus
        return f"Gained {self.defense_bonus} defense points"

class Sword(Item):
    def __init__(self, item_data):
        super().__init__(item_data)
        self.image = pygame.transform.scale(
            pygame.image.load("client/assets/items/sword.png").convert_alpha(),
            (24, 24))
        self.attack_bonus = int(self.value * 20)
    
    def use(self, player):
        """Increase attack damage"""
        player['attack_bonus'] = self.attack_bonus
        return f"Attack increased by {self.attack_bonus} points"

class Coin(Item):
    def __init__(self, item_data):
        super().__init__(item_data)
        self.image = pygame.transform.scale(
            pygame.image.load("client/assets/items/key.png").convert_alpha(),
            (24, 24))
        self.coin_value = int(self.value * 100)
    
    def use(self, player):
        """Add coins to player's inventory"""
        if 'coins' not in player:
            player['coins'] = 0
        player['coins'] += self.coin_value
        return f"Collected {self.coin_value} coins"

class ManaPotion(Item):
    def __init__(self, item_data):
        super().__init__(item_data)
        self.image = pygame.transform.scale(
            pygame.image.load("client/assets/items/mana_potion.png").convert_alpha(),
            (24, 24))
        self.mana_amount = int(item_data.get('value', 0.5) * 50)
    
    def use(self, player):
        """Trigger mana restoration through network"""
        from .game import NetworkClient
        
        # Find NetworkClient instance
        import inspect
        for frame_record in inspect.stack():
            frame = frame_record.frame
            if 'self' in frame.f_locals:
                obj = frame.f_locals['self']
                if isinstance(obj, NetworkClient):
                    obj.send({
                        "type": "use_item", 
                        "data": {
                            "item_type": "mana_potion", 
                            "mana_amount": self.mana_amount
                        }
                    })
                    break
        return f"Restoring {self.mana_amount} mana"
    
def create_item(item_data):
    """Factory method to create specific item types"""
    item_type_map = {
        "potion": HealPotion,
        "mana_potion": ManaPotion,
        "shield": Shield,
        "sword": Sword,
        "coin": Coin
    }

    item_class = item_type_map.get(item_data['type'], Item)
    return item_class(item_data)