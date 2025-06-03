import pygame

class Map:
    def __init__(self, tile_size=64):
        self.tile_size = tile_size
        self.layout = [
            [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8],
            [8,0,0,0,0,4,0,0,12,0,0,0,4,0,0,4,0,0,0,8],
            [8,0,1,1,0,4,0,7,0,0,12,0,0,7,0,4,0,3,0,8],
            [8,0,1,1,0,4,0,0,0,0,0,0,0,0,0,4,0,3,0,8],
            [8,0,0,1,0,0,0,0,5,5,0,5,5,0,0,0,0,3,0,8],
            [8,0,12,0,0,0,7,0,0,0,0,0,0,0,0,0,0,0,0,8],
            [8,0,10,10,10,0,0,7,0,0,12,0,0,7,0,0,10,10,10,8],
            [8,0,10,10,10,0,0,0,0,0,0,0,0,0,0,0,10,10,10,8],
            [8,0,0,0,0,0,0,0,4,0,4,0,0,0,0,0,0,0,0,8],
            [8,0,0,0,0,5,0,0,0,0,0,0,0,0,6,0,0,0,0,8],
            [8,0,0,7,0,0,0,4,0,0,0,0,4,0,0,0,0,0,0,8],
            [8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,12,0,0,0,8],
            [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
        ]
    
        self.width = len(self.layout[0])
        self.height = len(self.layout)
        
        self.tile_definitions = {
            0: {"type": "grass", "passable": True},
            1: {"type": "dirt_path", "passable": True},
            2: {"type": "sand", "passable": True},
            3: {"type": "cobblestone", "passable": True},
            4: {"type": "oak_tree", "passable": False},
            5: {"type": "pine_tree", "passable": False},
            6: {"type": "dead_tree", "passable": False},
            7: {"type": "rock", "passable": False},
            8: {"type": "stone_wall", "passable": False},
            9: {"type": "wooden_fence", "passable": False},
            10: {"type": "water", "passable": False},
            11: {"type": "deep_water", "passable": False},
            12: {"type": "bush", "passable": False},
        }

        self.tiles = self.initialize_tiles()
        self.grass_texture = None

        self.load_textures()

    def initialize_tiles(self):
        """Create tile grid with proper properties"""
        tiles = []
        for row in self.layout:
            tile_row = []
            for tile_id in row:
                tile_data = self.tile_definitions.get(tile_id, {"type": "unknown", "passable": False})
                tile_row.append({
                    "type": tile_data["type"],
                    "passable": tile_data["passable"],
                    "id": tile_id
                })
            tiles.append(tile_row)
        return tiles
    
    def load_textures(self):
        self.grass_texture = pygame.image.load("client/assets/map/terrain/grass.png").convert_alpha()
        self.grass_texture = pygame.transform.scale(self.grass_texture, 
                                                  (self.tile_size, self.tile_size))
        
        self.tile_textures = {
            0: pygame.image.load("client/assets/map/terrain/grass.png"),
            1: pygame.image.load("client/assets/map/terrain/dirt_path.png"),
            2: pygame.image.load("client/assets/map/terrain/sand.png"),
            3: pygame.image.load("client/assets/map/terrain/cobblestone_path.png"),
            4: pygame.image.load("client/assets/map/obstacles/oak_tree.png"),
            5: pygame.image.load("client/assets/map/obstacles/pine_tree.png"),
            6: pygame.image.load("client/assets/map/obstacles/dead_tree.png"),
            7: pygame.image.load("client/assets/map/obstacles/rock_large.png"),
            8: pygame.image.load("client/assets/map/obstacles/stone_wall.png"),
            9: pygame.image.load("client/assets/map/obstacles/wooden_fence.png"),
            10: pygame.image.load("client/assets/map/terrain/water.png"),
            11: pygame.image.load("client/assets/map/terrain/deep_water.png"),
            12: pygame.image.load("client/assets/map/obstacles/bush.png"),
        }
        # Scale textures to tile size
        for key in self.tile_textures:
            if isinstance(self.tile_textures[key], pygame.Surface):
                self.tile_textures[key] = pygame.transform.scale(
                    self.tile_textures[key], 
                    (self.tile_size, self.tile_size)
                )
            else:
                self.tile_textures[key] = [
                    pygame.transform.scale(tex, (self.tile_size, self.tile_size))
                    for tex in self.tile_textures[key]
                ]

    def draw(self, screen, view_x, view_y):
        screen_width, screen_height = screen.get_size()
        
        start_x = max(0, view_x // self.tile_size)
        start_y = max(0, view_y // self.tile_size)
        end_x = min(self.width, (view_x + screen_width) // self.tile_size + 1)
        end_y = min(self.height, (view_y + screen_height) // self.tile_size + 1)
        
         # First draw grass base layer for all visible tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x = x * self.tile_size - view_x
                screen_y = y * self.tile_size - view_y
                screen.blit(self.grass_texture, (screen_x, screen_y))
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_id = self.layout[y][x]
                if tile_id == 0:  # Skip grass tiles
                    continue
                
                if tile_id in self.tile_textures:
                    texture = self.tile_textures[tile_id]
                    screen.blit(texture,
                               (x * self.tile_size - view_x,
                                y * self.tile_size - view_y))