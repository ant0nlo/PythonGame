# client/main.py

from .game import Game
from .home_screen import HomeScreen

def main():
    """Standalone entry point for the home screen."""
    home_screen = HomeScreen()
    result = home_screen.run()
    
    if result[0]:
        username, avatar_name = result

        avatar_to_class = {
            "Warrior": "warrior",
            "Mage": "mage",
            "Archer": "archer"
        }

        hero_class = avatar_to_class.get(avatar_name, "warrior")

        game = Game(username, avatar_name, hero_class)
        game.run()
        
if __name__ == "__main__":
    main()
