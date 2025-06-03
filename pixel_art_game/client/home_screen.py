# client/home_screen.py

import pygame
import sys
import os

class HomeScreen:
    def __init__(self, screen_width=800, screen_height=600):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Adventure Game - Character Setup")
        self.background_image = self.load_background_image()
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        self.COLOR_INACTIVE = pygame.Color('lightskyblue3')
        self.COLOR_ACTIVE = pygame.Color('dodgerblue2')
        self.BUTTON_INACTIVE = (70, 130, 180)
        self.BUTTON_ACTIVE = (100, 160, 210)
        self.TEXT_COLOR = (255, 255, 255)
        self.SCREEN_CENTER_X = screen_width // 2
        self.avatars = ["Warrior", "Mage", "Archer"]
        self.clock = pygame.time.Clock()

    def load_background_image(self):
        try:
            image_path = os.path.join("client", "assets", "backgrounds", "main_background.jpg")
            image = pygame.image.load(image_path).convert()
            return pygame.transform.scale(image, (self.screen_width, self.screen_height))
        except Exception as e:
            print(f"Error loading background image: {e}")
            return pygame.Surface((self.screen_width, self.screen_height))

    def draw_image_background(self):
        self.screen.blit(self.background_image, (0, 0))

    def create_button(self, text, x, y, width, height):
        mouse = pygame.mouse.get_pos()
        button_rect = pygame.Rect(x, y, width, height)
        is_hover = button_rect.collidepoint(mouse)
        current_color = self.BUTTON_ACTIVE if is_hover else self.BUTTON_INACTIVE
        button_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(button_surface, current_color + (200,), (0, 0, width, height), border_radius=10)
        pygame.draw.rect(button_surface, (255, 255, 255, 100), (0, 0, width, height), width=2, border_radius=10)
        self.screen.blit(button_surface, (x, y))
        text_surf = self.font.render(text, True, self.TEXT_COLOR)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)
        return button_rect, is_hover

    def run(self):
        input_box_width, input_box_height = 400, 50
        input_box = pygame.Rect(
            self.SCREEN_CENTER_X - input_box_width // 2, 
            300, 
            input_box_width, 
            input_box_height
        )
        input_color = self.COLOR_INACTIVE
        active = False
        username = ""
        selected_avatar_index = 0
        left_arrow_rect = pygame.Rect(
            self.SCREEN_CENTER_X - 200, 
            400, 
            50, 
            50
        )
        right_arrow_rect = pygame.Rect(
            self.SCREEN_CENTER_X + 150, 
            400, 
            50, 
            50
        )
        done = False
        start_game = False

        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if input_box.collidepoint(event.pos):
                        active = True
                        input_color = self.COLOR_ACTIVE
                    else:
                        active = False
                        input_color = self.COLOR_INACTIVE
                    if left_arrow_rect.collidepoint(event.pos):
                        selected_avatar_index = (selected_avatar_index - 1) % len(self.avatars)
                    elif right_arrow_rect.collidepoint(event.pos):
                        selected_avatar_index = (selected_avatar_index + 1) % len(self.avatars)
                if event.type == pygame.KEYDOWN:
                    if active:
                        if event.key == pygame.K_BACKSPACE:
                            username = username[:-1]
                        elif event.key == pygame.K_RETURN:
                            active = False
                            input_color = self.COLOR_INACTIVE
                        else:
                            if event.unicode.isprintable() and len(username) < 15:
                                username += event.unicode

            self.draw_image_background()
            title_surface = self.title_font.render("Adventure Awaits!", True, self.TEXT_COLOR)
            title_rect = title_surface.get_rect(center=(self.SCREEN_CENTER_X, 100))
            self.screen.blit(title_surface, title_rect)
            subtitle_text = "Create Your Hero"
            subtitle_surface = self.subtitle_font.render(subtitle_text, True, self.TEXT_COLOR)
            subtitle_rect = subtitle_surface.get_rect(center=(self.SCREEN_CENTER_X, 180))
            self.screen.blit(subtitle_surface, subtitle_rect)
            pygame.draw.rect(self.screen, input_color, input_box, 2)
            username_label = self.font.render("Enter Username:", True, self.TEXT_COLOR)
            username_label_rect = username_label.get_rect(center=(self.SCREEN_CENTER_X, 270))
            self.screen.blit(username_label, username_label_rect)
            txt_surface = self.font.render(username, True, self.TEXT_COLOR)
            txt_rect = txt_surface.get_rect(center=input_box.center)
            self.screen.blit(txt_surface, txt_rect)
            hero_label = self.font.render("Choose Your Hero:", True, self.TEXT_COLOR)
            hero_label_rect = hero_label.get_rect(center=(self.SCREEN_CENTER_X, 370))
            self.screen.blit(hero_label, hero_label_rect)
            avatar_text = self.avatars[selected_avatar_index]
            avatar_surface = self.font.render(avatar_text, True, self.TEXT_COLOR)
            avatar_rect = avatar_surface.get_rect(center=(self.SCREEN_CENTER_X, 430))
            self.screen.blit(avatar_surface, avatar_rect)
            arrow_font = pygame.font.Font(None, 48)
            left_arrow = arrow_font.render("◀", True, (255, 255, 0))
            right_arrow = arrow_font.render("▶", True, (255, 255, 0))
            self.screen.blit(left_arrow, left_arrow_rect.topleft)
            self.screen.blit(right_arrow, right_arrow_rect.topleft)
            start_button_rect, start_hover = self.create_button(
                "Start Adventure", 
                self.SCREEN_CENTER_X - 100, 
                500, 
                200, 
                50
            )
            mouse_click = pygame.mouse.get_pressed()
            if start_hover and mouse_click[0] and username.strip():
                start_game = True
                done = True
            pygame.display.flip()
            self.clock.tick(30)

        return (username, self.avatars[selected_avatar_index]) if start_game else (None, None)
