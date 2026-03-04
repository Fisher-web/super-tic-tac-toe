import pygame
import sys
import requests
import os
import threading
import websocket
import json
import time
import random
import string
from game import SuperTicTacToe
from animations import Animation, PulseAnimation, FadeAnimation

# Константы
SCREEN_WIDTH = 360
SCREEN_HEIGHT = 640
CELL_SIZE = 35
BOARD_SIZE = CELL_SIZE * 9

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
GOLD = (255, 215, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
BG_COLOR = (59, 131, 189)

class Avatar:
    def __init__(self, x, y, size=80):
        self.rect = pygame.Rect(x, y, size, size)
        self.size = size
        self.color = (200, 200, 200)
        
    def draw(self, screen, frame='none'):
        pygame.draw.circle(screen, self.color, self.rect.center, self.size//2)
        pygame.draw.circle(screen, BLACK, self.rect.center, self.size//2, 2)
        
        font = pygame.font.Font(None, 40)
        avatar_text = font.render("👤", True, BLACK)
        text_rect = avatar_text.get_rect(center=self.rect.center)
        screen.blit(avatar_text, text_rect)
        
        if frame == 'bronze':
            pygame.draw.circle(screen, (205, 127, 50), self.rect.center, self.size//2 + 3, 4)
        elif frame == 'silver':
            pygame.draw.circle(screen, (192, 192, 192), self.rect.center, self.size//2 + 3, 4)
        elif frame == 'gold':
            pygame.draw.circle(screen, (255, 215, 0), self.rect.center, self.size//2 + 3, 4)

class Button:
    def __init__(self, x, y, w, h, text, color=GRAY, text_color=BLACK, font_size=24, icon=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font_size = font_size
        self.icon = icon
        
        self.original_color = color
        self.hover_color = tuple(min(255, c + 30) for c in color)
        self.press_color = tuple(max(0, c - 30) for c in color)
        
        self.is_hovered = False
        self.is_pressed = False
        self.animation = None
        
        self.shadow_offset = 3
        self.shadow_color = (0, 0, 0, 50)
        
    def draw(self, screen, font):
        shadow_rect = self.rect.copy()
        shadow_rect.x += self.shadow_offset
        shadow_rect.y += self.shadow_offset
        shadow_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 50))
        screen.blit(shadow_surf, shadow_rect)
        
        current_color = self.color
        if self.is_pressed:
            current_color = self.press_color
        elif self.is_hovered:
            current_color = self.hover_color
            
        gradient = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        for y in range(self.rect.height):
            alpha = int(255 * (1 - y / self.rect.height * 0.3))
            color_with_alpha = (*current_color, alpha)
            pygame.draw.line(gradient, color_with_alpha, (0, y), (self.rect.width, y))
        
        screen.blit(gradient, self.rect)
        pygame.draw.rect(screen, current_color, self.rect, 2, border_radius=8)
        
        if self.icon:
            icon_surf = font.render(self.icon, True, self.text_color)
            icon_rect = icon_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
            screen.blit(icon_surf, icon_rect)
        
        text_surf = font.render(self.text, True, self.text_color)
        if self.icon:
            text_rect = text_surf.get_rect(midleft=(self.rect.x + 35, self.rect.centery))
        else:
            text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def update(self, mouse_pos, mouse_clicked):
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        if self.is_hovered and not was_hovered:
            self.animation = PulseAnimation(self, 1.05, 0.2)
            self.animation.start()
        
        self.is_pressed = self.is_hovered and mouse_clicked
        
        if self.animation:
            self.animation.update()
    
    def is_clicked(self, pos, mouse_clicked):
        return self.rect.collidepoint(pos) and mouse_clicked

class Background:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.particles = []
        self.create_particles()
        
    def create_particles(self):
        for _ in range(20):
            self.particles.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'speed': random.uniform(0.1, 0.5),
                'size': random.randint(2, 5),
                'alpha': random.randint(50, 150)
            })
    
    def update(self):
        for p in self.particles:
            p['y'] -= p['speed']
            if p['y'] < 0:
                p['y'] = self.height
                p['x'] = random.randint(0, self.width)
    
    def draw(self, screen):
        for y in range(self.height):
            color_value = int(59 + (y / self.height) * 50)
            color = (color_value, 131, 189)
            pygame.draw.line(screen, color, (0, y), (self.width, y))
        
        for p in self.particles:
            surf = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255, p['alpha']), 
                              (p['size'], p['size']), p['size'])
            screen.blit(surf, (p['x'], p['y']))

class Toast:
    def __init__(self, text, duration=2.0, color=GREEN):
        self.text = text
        self.duration = duration * 60
        self.current_time = 0
        self.color = color
        self.is_active = True
        self.alpha = 0
        
    def update(self):
        if self.is_active:
            self.current_time += 1
            if self.current_time > self.duration:
                self.is_active = False
            
            if self.current_time < 20:
                self.alpha = int((self.current_time / 20) * 255)
            elif self.current_time > self.duration - 20:
                remaining = self.duration - self.current_time
                self.alpha = int((remaining / 20) * 255)
            else:
                self.alpha = 255
    
    def draw(self, screen, font, x, y):
        if not self.is_active:
            return
        
        text_surf = font.render(self.text, True, self.color)
        text_rect = text_surf.get_rect(center=(x, y))
        
        bg_rect = text_rect.inflate(20, 10)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((255, 255, 255, self.alpha))
        screen.blit(bg_surf, bg_rect)
        
        pygame.draw.rect(screen, (*self.color, self.alpha), bg_rect, 2, border_radius=5)
        
        text_surf.set_alpha(self.alpha)
        screen.blit(text_surf, text_rect)

class Keyboard:
    def __init__(self):
        self.keys = []
        self.active = False
        self.current_input = ""
        self.create_keys()
    
    def create_keys(self):
        rows = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm', '.', '_', '-'],
        ]
        
        y_start = 350
        key_w = 35
        key_h = 40
        
        for row_idx, row in enumerate(rows):
            total_width = len(row) * key_w
            x_start = (SCREEN_WIDTH - total_width) // 2
            for col_idx, key in enumerate(row):
                x = x_start + col_idx * key_w
                y = y_start + row_idx * key_h
                btn = Button(x, y, key_w, key_h, key, LIGHT_GRAY, BLACK, 20)
                self.keys.append(btn)
        
        y_bottom = y_start + 4 * key_h + 10
        self.keys.append(Button(30, y_bottom, 60, key_h, '⌫', RED, WHITE, 20))
        self.keys.append(Button(105, y_bottom, 150, key_h, ' ', LIGHT_GRAY, BLACK, 20))
        self.keys.append(Button(270, y_bottom, 60, key_h, '✓', GREEN, WHITE, 20))
    
    def handle_click(self, pos):
        if not self.active:
            return None
        for key in self.keys:
            if key.is_clicked(pos, True):
                if key.text == '⌫':
                    self.current_input = self.current_input[:-1]
                elif key.text == '✓':
                    self.active = False
                    result = self.current_input
                    self.current_input = ""
                    return result
                elif key.text == ' ':
                    self.current_input += ' '
                else:
                    self.current_input += key.text
                return None
        return None
    
    def draw(self, screen, font, mouse_pos, mouse_clicked):
        if not self.active:
            return
        if self.current_input:
            input_surf = font.render(self.current_input, True, BLACK)
            pygame.draw.rect(screen, WHITE, (50, 315, 260, 30))
            pygame.draw.rect(screen, BLUE, (50, 315, 260, 30), 2)
            screen.blit(input_surf, (55, 320))
        
        for key in self.keys:
            key.update(mouse_pos, mouse_clicked)
            key.draw(screen, font)

class OnlineManager:
    def __init__(self, game_callback):
        self.ws = None
        self.connected = False
        self.game_callback = game_callback
        self.message_queue = []
        self.current_game_id = None
        self.opponent_id = None
        
    def connect(self, userId):
        def on_message(ws, message):
            data = json.loads(message)
            self.game_callback(data)
            
        def on_error(ws, error):
            print(f"WebSocket ошибка: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            self.connected = False
            print("Соединение закрыто")
            
        def on_open(ws):
            self.connected = True
            print("Подключено к серверу")
            for msg in self.message_queue:
                ws.send(json.dumps(msg))
            self.message_queue.clear()
        
        self.ws = websocket.WebSocketApp("ws://192.168.1.104:3001",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()
        
    def send(self, data):
        if self.ws and self.connected:
            self.ws.send(json.dumps(data))
        else:
            self.message_queue.append(data)
    
    def find_game(self, userId, bet=0):
        self.send({'type': 'find_game', 'userId': userId, 'bet': bet})
    
    def create_room(self, userId, bet=0):
        self.send({'type': 'create_room', 'userId': userId, 'bet': bet})
    
    def join_room(self, roomId, userId):
        self.send({'type': 'join_room', 'roomId': roomId, 'userId': userId})
    
    def make_move(self, gameId, move):
        self.send({'type': 'make_move', 'gameId': gameId, 'move': move})
    
    def game_over(self, gameId, winner, gameData):
        self.send({'type': 'game_over', 'gameId': gameId, 'winner': winner, 'gameData': gameData})

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Tic-Tac-Toe")
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.big_font = pygame.font.Font(None, 28)
        
        self.game = SuperTicTacToe()
        self.api_url = "http://192.168.1.104:3001/api"
        
        self.player_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        self.user = None
        self.state = "welcome"
        self.message = ""
        self.message_time = 0
        
        self.background = Background(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.toasts = []
        self.transition_alpha = 0
        self.transition_direction = None
        
        self.keyboard = Keyboard()
        self.current_field = None
        
        self.reg_username = ""
        self.reg_password = ""
        self.reg_confirm = ""
        
        self.login_username = ""
        self.login_password = ""
        
        self.online = OnlineManager(self.handle_online_message)
        self.room_id = ""
        self.bet_amount = 0
        self.is_my_turn = False
        self.waiting_for_opponent = False
        self.online_game_id = None
        
        self.current_season = {"name": "Сезон 1", "days_left": 15}
        self.hall_of_fame = []
        self.friends = []
        self.notifications = []
        self.achievements = []
        
        self.load_season_info()
    
    def load_season_info(self):
        self.current_season = {
            "name": "Сезон 2",
            "days_left": 15,
            "player_place": 42
        }
        
        self.hall_of_fame = [
            {"season": 2, "winner": "Player_K7F9", "rating": 1450, "comment": "Лучший сезон в моей жизни!"},
            {"season": 1, "winner": "Champion_X", "rating": 1380, "comment": "Неплохо для начала"}
        ]
    
    def create_menu_ui(self):
        self.buttons = [
            Button(30, 200, 300, 40, "Локальная игра", GREEN, BLACK, 22, "🎮"),
            Button(30, 250, 300, 40, "Играть онлайн", BLUE, WHITE, 22, "🌐"),
            Button(30, 300, 300, 40, "Аллея славы", GOLD, BLACK, 20, "🏆"),
            Button(30, 350, 300, 40, "Достижения", PURPLE, WHITE, 20, "🏅"),
            Button(30, 400, 300, 40, "Социальное", ORANGE, BLACK, 20, "👥"),
            Button(30, 450, 300, 40, "Поддержать", (255, 215, 0), BLACK, 20, "💰"),
            Button(30, 500, 300, 40, "Профиль", GRAY, BLACK, 20, "👤"),
            Button(30, 550, 300, 30, "Выход", RED, WHITE, 18, "❌")
        ]
    
    def create_online_menu(self):
        self.buttons = [
            Button(30, 150, 300, 40, "Случайный поиск", GREEN, BLACK, 22, "🎲"),
            Button(30, 200, 300, 40, "Создать комнату", BLUE, WHITE, 22, "🔗"),
            Button(30, 250, 300, 40, "Присоединиться", PURPLE, WHITE, 22, "🚪"),
            Button(30, 350, 140, 30, "-100", RED, WHITE, 20),
            Button(190, 350, 140, 30, "+100", GREEN, BLACK, 20),
            Button(30, 400, 300, 30, "Назад", GRAY, BLACK, 20, "◀️")
        ]
    
    def create_social_menu(self):
        self.buttons = [
            Button(30, 150, 300, 40, "Друзья", GREEN, BLACK, 22, "👥"),
            Button(30, 200, 300, 40, "Чаты", BLUE, WHITE, 22, "💬"),
            Button(30, 250, 300, 40, "Уведомления", GOLD, BLACK, 22, "🔔"),
            Button(30, 350, 300, 30, "Назад", GRAY, BLACK, 20, "◀️")
        ]
    
    def show_message(self, text, color=GREEN):
        self.toasts.append(Toast(text, 2.0, color))
    
    def start_transition(self):
        self.transition_direction = 'in'
    
    def handle_online_message(self, data):
        msg_type = data.get('type')
        print(f"Получено: {msg_type}")
        
        if msg_type == 'game_found':
            self.online_game_id = data['gameId']
            self.opponent_id = data['opponentId']
            self.is_my_turn = data['yourTurn']
            self.waiting_for_opponent = False
            self.game.reset()
            self.game.current_player = 1 if self.is_my_turn else 2
            self.state = "online_game"
            self.show_message("Противник найден!")
            
        elif msg_type == 'waiting':
            self.waiting_for_opponent = True
            self.show_message("Ищем соперника...", BLUE)
            
        elif msg_type == 'room_created':
            self.room_id = data['roomId']
            self.waiting_for_opponent = True
            self.show_message(f"Комната создана! ID: {self.room_id}", GREEN)
            
        elif msg_type == 'player_joined':
            self.waiting_for_opponent = False
            self.opponent_id = data['opponentId']
            self.game.reset()
            self.game.current_player = 1
            self.is_my_turn = True
            self.state = "online_game"
            self.show_message("Противник присоединился!", GREEN)
            
        elif msg_type == 'game_start':
            self.online_game_id = data['gameId']
            self.opponent_id = data['opponentId']
            self.is_my_turn = data['yourTurn']
            self.game.reset()
            self.game.current_player = 1 if self.is_my_turn else 2
            self.state = "online_game"
            self.show_message("Игра началась!", GREEN)
            
        elif msg_type == 'opponent_move':
            move = data['move']
            self.game.make_move(move['row'], move['col'])
            self.is_my_turn = True
            
        elif msg_type == 'opponent_disconnected':
            self.show_message("Противник отключился", RED)
            self.state = "online_menu"
            
        elif msg_type == 'game_ended':
            if data.get('winner'):
                self.show_message("Игра завершена!", GOLD)
            self.state = "online_menu"
    
    def handle_click(self, pos):
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        if self.keyboard.active:
            result = self.keyboard.handle_click(pos)
            if result is not None:
                if self.state == "register":
                    if self.current_field == "reg_username":
                        self.reg_username = result
                        self.current_field = "reg_password"
                        self.keyboard.current_input = ""
                        self.keyboard.active = True
                    elif self.current_field == "reg_password":
                        self.reg_password = result
                        self.current_field = "reg_confirm"
                        self.keyboard.current_input = ""
                        self.keyboard.active = True
                    elif self.current_field == "reg_confirm":
                        self.reg_confirm = result
                        self.keyboard.current_input = ""
                        self.keyboard.active = False
                        self.register()
                elif self.state == "login":
                    if self.current_field == "login_username":
                        self.login_username = result
                        self.current_field = "login_password"
                        self.keyboard.current_input = ""
                        self.keyboard.active = True
                    elif self.current_field == "login_password":
                        self.login_password = result
                        self.keyboard.current_input = ""
                        self.keyboard.active = False
                        self.login()
                elif self.state == "join_room":
                    self.room_id = result
                    if self.user:
                        self.online.join_room(self.room_id, self.user['id'])
                        self.state = "online_menu"
                        self.waiting_for_opponent = True
                        self.show_message("Присоединяемся к комнате...", PURPLE)
                elif self.state == "edit_nickname":
                    self.user['username'] = result
                    self.show_message(f"Ник изменен на {result}", GREEN)
                    self.state = "profile"
                    self.keyboard.active = False
                    self.current_field = None
            return
        
        if self.state == "welcome":
            buttons = [
                (pygame.Rect(30, 200, 300, 50), "welcome_login"),
                (pygame.Rect(30, 270, 300, 50), "welcome_register"),
                (pygame.Rect(30, 340, 300, 50), "welcome_guest")
            ]
            
            for rect, action in buttons:
                if rect.collidepoint(pos) and mouse_clicked:
                    self.start_transition()
                    if action == "welcome_login":
                        self.state = "login"
                        self.current_field = "login_username"
                    elif action == "welcome_register":
                        self.state = "register"
                        self.current_field = "reg_username"
                    elif action == "welcome_guest":
                        self.guest_login()
        
        elif self.state == "login":
            if 10 <= pos[0] <= 80 and 10 <= pos[1] <= 40:
                self.state = "welcome"
                return
            
            fields = [
                (pygame.Rect(50, 125, 260, 40), "login_username"),
                (pygame.Rect(50, 205, 260, 40), "login_password")
            ]
            
            for rect, field in fields:
                if rect.collidepoint(pos) and mouse_clicked:
                    self.keyboard.active = True
                    self.keyboard.current_input = getattr(self, field)
                    self.current_field = field
                    return
            
            login_btn = pygame.Rect(30, 280, 300, 40)
            if login_btn.collidepoint(pos) and mouse_clicked:
                self.login()
        
        elif self.state == "register":
            if 10 <= pos[0] <= 80 and 10 <= pos[1] <= 40:
                self.state = "welcome"
                return
            
            fields = [
                (pygame.Rect(50, 105, 260, 40), "reg_username"),
                (pygame.Rect(50, 185, 260, 40), "reg_password"),
                (pygame.Rect(50, 265, 260, 40), "reg_confirm")
            ]
            
            for rect, field in fields:
                if rect.collidepoint(pos) and mouse_clicked:
                    self.keyboard.active = True
                    self.keyboard.current_input = getattr(self, field)
                    self.current_field = field
                    return
            
            register_btn = pygame.Rect(30, 340, 300, 40)
            if register_btn.collidepoint(pos) and mouse_clicked:
                self.register()
        
        elif self.state == "menu":
            for button in self.buttons:
                if button.is_clicked(pos, mouse_clicked):
                    self.start_transition()
                    if button.text == "Локальная игра":
                        self.state = "playing"
                        self.game.reset()
                    elif button.text == "Играть онлайн":
                        if self.user:
                            self.state = "online_menu"
                            self.create_online_menu()
                            self.waiting_for_opponent = False
                            self.room_id = ""
                        else:
                            self.show_message("Сначала войдите в игру", RED)
                    elif button.text == "Аллея славы":
                        self.state = "hall_of_fame"
                    elif button.text == "Достижения":
                        self.state = "achievements"
                    elif button.text == "Социальное":
                        self.state = "social_menu"
                        self.create_social_menu()
                    elif button.text == "Поддержать":
                        if self.user:
                            self.show_message("Поддержка через @supertictactoe_donate_bot", BLUE)
                        else:
                            self.show_message("Сначала войдите в игру", RED)
                    elif button.text == "Профиль":
                        if self.user:
                            self.state = "profile"
                        else:
                            self.show_message("Сначала войдите в игру", RED)
                    elif button.text == "Выход":
                        self.user = None
                        self.state = "welcome"
        
        elif self.state == "online_menu":
            for button in self.buttons:
                if button.is_clicked(pos, mouse_clicked):
                    if button.text == "Случайный поиск":
                        if self.user:
                            self.show_message("🔍 Ищем соперника...", BLUE)
                            self.online.find_game(self.user['id'], self.bet_amount)
                            self.waiting_for_opponent = True
                        else:
                            self.show_message("Сначала войди в игру", RED)
                    elif button.text == "Создать комнату":
                        if self.user:
                            self.show_message("📋 Создаем комнату...", BLUE)
                            self.online.create_room(self.user['id'], self.bet_amount)
                        else:
                            self.show_message("Сначала войди в игру", RED)
                    elif button.text == "Присоединиться":
                        if self.user:
                            self.state = "join_room"
                            self.keyboard.active = True
                            self.keyboard.current_input = ""
                            self.current_field = "join_room"
                            self.show_message("🔑 Введите ID комнаты", PURPLE)
                        else:
                            self.show_message("Сначала войди в игру", RED)
                    elif button.text == "-100":
                        self.bet_amount = max(0, self.bet_amount - 100)
                        self.show_message(f"Ставка: {self.bet_amount}", GOLD)
                    elif button.text == "+100":
                        self.bet_amount += 100
                        self.show_message(f"Ставка: {self.bet_amount}", GOLD)
                    elif button.text == "Назад":
                        self.state = "menu"
                        self.waiting_for_opponent = False
                        self.room_id = ""
        
        elif self.state == "social_menu":
            for button in self.buttons:
                if button.is_clicked(pos, mouse_clicked):
                    if button.text == "Друзья":
                        self.state = "friends"
                    elif button.text == "Чаты":
                        self.state = "chats"
                    elif button.text == "Уведомления":
                        self.state = "notifications"
                    elif button.text == "Назад":
                        self.state = "menu"
        
        elif self.state == "profile":
            if 10 <= pos[0] <= 80 and 10 <= pos[1] <= 40:
                self.state = "menu"
            
            edit_nick_rect = pygame.Rect(250, 200, 80, 30)
            if edit_nick_rect.collidepoint(pos) and mouse_clicked:
                self.state = "edit_nickname"
                self.keyboard.active = True
                self.keyboard.current_input = self.user['username']
                self.current_field = "edit_nickname"
        
        elif self.state == "edit_nickname":
            if 10 <= pos[0] <= 80 and 10 <= pos[1] <= 40:
                self.state = "profile"
                self.keyboard.active = False
                self.current_field = None
        
        elif self.state == "playing":
            x, y = pos
            if y < BOARD_SIZE + 20:
                col = x // CELL_SIZE
                row = (y - 20) // CELL_SIZE
                if 0 <= row < 9 and 0 <= col < 9:
                    self.game.make_move(row, col)
            elif 280 <= x <= 350 and 580 <= y <= 610:
                self.state = "menu"
        
        elif self.state == "online_game":
            x, y = pos
            if y < BOARD_SIZE + 20 and self.is_my_turn:
                col = x // CELL_SIZE
                row = (y - 20) // CELL_SIZE
                if 0 <= row < 9 and 0 <= col < 9:
                    success, msg = self.game.make_move(row, col)
                    if success and self.online_game_id:
                        self.online.make_move(self.online_game_id, {'row': row, 'col': col})
                        self.is_my_turn = False
                        if self.game.game_over and self.online_game_id:
                            winner_id = self.user['id'] if self.game.winner == 1 else None
                            self.online.game_over(self.online_game_id, winner_id, self.game.get_state())
                            self.show_message("Игра завершена!", GOLD)
            elif 280 <= x <= 350 and 580 <= y <= 610:
                self.state = "online_menu"
                self.waiting_for_opponent = False
        
        elif self.state == "join_room":
            if 10 <= pos[0] <= 80 and 10 <= pos[1] <= 40:
                self.state = "online_menu"
                self.keyboard.active = False
                self.current_field = None
        
        elif self.state == "hall_of_fame":
            if 10 <= pos[0] <= 80 and 10 <= pos[1] <= 40:
                self.state = "menu"
        
        elif self.state == "achievements":
            if 10 <= pos[0] <= 80 and 10 <= pos[1] <= 40:
                self.state = "menu"
    
    def guest_login(self):
        try:
            response = requests.post(f"{self.api_url}/guest-login")
            data = response.json()
            if data.get("success"):
                self.user = data["user"]
                self.online.connect(self.user['id'])
                self.show_message(f"Добро пожаловать, {self.user['username']}!", GREEN)
                self.state = "menu"
                self.create_menu_ui()
            else:
                self.show_message("Ошибка входа", RED)
        except Exception as e:
            print(f"Ошибка: {e}")
            self.show_message("Ошибка подключения", RED)
    
    def login(self):
        if not self.login_username or not self.login_password:
            self.show_message("Введите имя и пароль", RED)
            return
        
        try:
            response = requests.post(f"{self.api_url}/login", json={
                "username": self.login_username,
                "password": self.login_password
            })
            data = response.json()
            if data.get("success"):
                self.user = data["user"]
                self.online.connect(self.user['id'])
                self.show_message(f"С возвращением, {self.user['username']}!", GREEN)
                self.state = "menu"
                self.create_menu_ui()
            else:
                self.show_message("Неверное имя или пароль", RED)
        except Exception as e:
            print(f"Ошибка: {e}")
            self.show_message("Ошибка подключения", RED)
    
    def register(self):
        if not self.reg_username or not self.reg_password:
            self.show_message("Заполните все поля", RED)
            return
        
        if self.reg_password != self.reg_confirm:
            self.show_message("Пароли не совпадают", RED)
            return
        
        if len(self.reg_password) < 3:
            self.show_message("Пароль слишком короткий", RED)
            return
        
        try:
            response = requests.post(f"{self.api_url}/register", json={
                "username": self.reg_username,
                "password": self.reg_password
            })
            data = response.json()
            if data.get("success"):
                self.user = data["user"]
                self.online.connect(self.user['id'])
                self.show_message(f"Добро пожаловать, {self.user['username']}!", GREEN)
                self.state = "menu"
                self.create_menu_ui()
            else:
                self.show_message(data.get("error", "Ошибка регистрации"), RED)
        except Exception as e:
            print(f"Ошибка: {e}")
            self.show_message("Ошибка подключения", RED)
    
    def draw(self):
        self.background.update()
        self.background.draw(self.screen)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        if self.state == "welcome":
            self.draw_welcome(mouse_pos, mouse_clicked)
        elif self.state == "login":
            self.draw_login(mouse_pos, mouse_clicked)
        elif self.state == "register":
            self.draw_register(mouse_pos, mouse_clicked)
        elif self.state == "menu":
            self.draw_menu(mouse_pos, mouse_clicked)
        elif self.state == "profile":
            self.draw_profile(mouse_pos, mouse_clicked)
        elif self.state == "edit_nickname":
            self.draw_edit_nickname(mouse_pos, mouse_clicked)
        elif self.state == "online_menu":
            self.draw_online_menu(mouse_pos, mouse_clicked)
        elif self.state == "join_room":
            self.draw_join_room(mouse_pos, mouse_clicked)
        elif self.state == "playing":
            self.draw_game("Локальная игра", mouse_pos, mouse_clicked)
        elif self.state == "online_game":
            self.draw_game("Онлайн игра", mouse_pos, mouse_clicked)
        elif self.state == "hall_of_fame":
            self.draw_hall_of_fame(mouse_pos, mouse_clicked)
        elif self.state == "social_menu":
            self.draw_social_menu(mouse_pos, mouse_clicked)
        elif self.state == "friends":
            self.draw_friends(mouse_pos, mouse_clicked)
        elif self.state == "chats":
            self.draw_chats(mouse_pos, mouse_clicked)
        elif self.state == "notifications":
            self.draw_notifications(mouse_pos, mouse_clicked)
        elif self.state == "achievements":
            self.draw_achievements(mouse_pos, mouse_clicked)
        
        for toast in self.toasts[:]:
            toast.update()
            toast.draw(self.screen, self.small_font, SCREEN_WIDTH//2, 100)
            if not toast.is_active:
                self.toasts.remove(toast)
        
        if self.transition_direction:
            self.draw_transition()
        
        pygame.display.flip()
    
    def draw_transition(self):
        if self.transition_direction == 'in':
            self.transition_alpha += 15
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                self.transition_direction = 'out'
        elif self.transition_direction == 'out':
            self.transition_alpha -= 15
            if self.transition_alpha <= 0:
                self.transition_alpha = 0
                self.transition_direction = None
        
        if self.transition_alpha > 0:
            surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            surf.fill((0, 0, 0, self.transition_alpha))
            self.screen.blit(surf, (0, 0))
    
    def draw_welcome(self, mouse_pos, mouse_clicked):
        title = self.big_font.render("Super Tic-Tac-Toe", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 80))
        shadow = self.big_font.render("Super Tic-Tac-Toe", True, (0,0,0,100))
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH//2 + 3, 83))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title, title_rect)
        
        buttons = [
            (pygame.Rect(30, 200, 300, 50), "🔑 Войти", BLUE),
            (pygame.Rect(30, 270, 300, 50), "📝 Регистрация", GREEN),
            (pygame.Rect(30, 340, 300, 50), "🎮 Играть как гость", GRAY)
        ]
        
        for rect, text, color in buttons:
            hovered = rect.collidepoint(mouse_pos)
            pressed = hovered and mouse_clicked
            
            if pressed:
                current_color = tuple(max(0, c - 30) for c in color)
            elif hovered:
                current_color = tuple(min(255, c + 30) for c in color)
            else:
                current_color = color
            
            shadow_rect = rect.copy()
            shadow_rect.x += 3
            shadow_rect.y += 3
            pygame.draw.rect(self.screen, (0,0,0,50), shadow_rect, border_radius=5)
            pygame.draw.rect(self.screen, current_color, rect, border_radius=5)
            pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=5)
            
            text_surf = self.font.render(text, True, WHITE)
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)
        
        tg_text = self.small_font.render("После входа можно привязать Telegram в профиле", True, WHITE)
        tg_rect = tg_text.get_rect(center=(SCREEN_WIDTH//2, 450))
        self.screen.blit(tg_text, tg_rect)
    
    def draw_login(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("ВХОД", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 50))
        self.screen.blit(title, title_rect)
        
        fields = [
            ("Имя:", 100, self.login_username, "login_username"),
            ("Пароль:", 180, self.login_password, "login_password")
        ]
        
        y_pos = 125
        for label, y_offset, value, field in fields:
            label_text = self.small_font.render(label, True, WHITE)
            self.screen.blit(label_text, (50, y_offset))
            
            rect = pygame.Rect(50, y_offset + 25, 260, 40)
            border_color = GREEN if self.current_field == field else BLUE
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, border_color, rect, 3)
            
            if field == "login_password":
                display = "*" * len(value) if value else "введите пароль"
            else:
                display = value if value else "введите имя"
            
            text = self.font.render(display, True, BLACK if value else GRAY)
            self.screen.blit(text, (55, y_offset + 30))
        
        login_btn = pygame.Rect(30, 280, 300, 40)
        hovered = login_btn.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            btn_color = (0,100,0)
        elif hovered:
            btn_color = (0,180,0)
        else:
            btn_color = GREEN
        
        pygame.draw.rect(self.screen, btn_color, login_btn, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, login_btn, 2, border_radius=5)
        btn_text = self.font.render("🚪 Войти", True, BLACK)
        btn_rect = btn_text.get_rect(center=login_btn.center)
        self.screen.blit(btn_text, btn_rect)
        
        self.keyboard.draw(self.screen, self.font, mouse_pos, mouse_clicked)
    
    def draw_register(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("РЕГИСТРАЦИЯ", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 50))
        self.screen.blit(title, title_rect)
        
        fields = [
            ("Имя:", 80, self.reg_username, "reg_username"),
            ("Пароль:", 160, self.reg_password, "reg_password"),
            ("Подтверждение:", 240, self.reg_confirm, "reg_confirm")
        ]
        
        y_pos = 105
        for label, y_offset, value, field in fields:
            label_text = self.small_font.render(label, True, WHITE)
            self.screen.blit(label_text, (50, y_offset))
            
            rect = pygame.Rect(50, y_offset + 25, 260, 40)
            border_color = GREEN if self.current_field == field else BLUE
            pygame.draw.rect(self.screen, WHITE, rect)
            pygame.draw.rect(self.screen, border_color, rect, 3)
            
            if field in ["reg_password", "reg_confirm"]:
                display = "*" * len(value) if value else "введите"
            else:
                display = value if value else "введите"
            
            text = self.font.render(display, True, BLACK if value else GRAY)
            self.screen.blit(text, (55, y_offset + 30))
        
        register_btn = pygame.Rect(30, 340, 300, 40)
        hovered = register_btn.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            btn_color = (0,100,0)
        elif hovered:
            btn_color = (0,180,0)
        else:
            btn_color = GREEN
        
        pygame.draw.rect(self.screen, btn_color, register_btn, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, register_btn, 2, border_radius=5)
        btn_text = self.font.render("✅ Зарегистрироваться", True, BLACK)
        btn_rect = btn_text.get_rect(center=register_btn.center)
        self.screen.blit(btn_text, btn_rect)
        
        self.keyboard.draw(self.screen, self.font, mouse_pos, mouse_clicked)
    
    def draw_menu(self, mouse_pos, mouse_clicked):
        title = self.big_font.render("Super Tic-Tac-Toe", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 40))
        shadow = self.big_font.render("Super Tic-Tac-Toe", True, (0,0,0,100))
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH//2 + 3, 43))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title, title_rect)
        
        season_info = self.small_font.render(f"🏆 {self.current_season['name']} • До конца: {self.current_season['days_left']} дней", True, GOLD)
        season_rect = season_info.get_rect(center=(SCREEN_WIDTH//2, 70))
        self.screen.blit(season_info, season_rect)
        
        if self.user:
            info_rect = pygame.Rect(20, 90, SCREEN_WIDTH-40, 70)
            shadow_rect = info_rect.copy()
            shadow_rect.x += 3
            shadow_rect.y += 3
            pygame.draw.rect(self.screen, (0,0,0,50), shadow_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255,255,255,200), info_rect, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, info_rect, 2, border_radius=10)
            
            avatar_rect = pygame.Rect(30, 95, 30, 30)
            pygame.draw.circle(self.screen, (200,200,200), avatar_rect.center, 15)
            avatar_text = self.small_font.render("👤", True, BLACK)
            avatar_rect_text = avatar_text.get_rect(center=avatar_rect.center)
            self.screen.blit(avatar_text, avatar_rect_text)
            
            name_text = self.font.render(self.user['username'], True, BLACK)
            self.screen.blit(name_text, (70, 100))
            
            coins_text = self.small_font.render(f"💰 {self.user['coins']}", True, GOLD)
            self.screen.blit(coins_text, (70, 125))
            
            rating_text = self.small_font.render(f"⭐ {self.user['rating']}", True, BLUE)
            self.screen.blit(rating_text, (250, 100))
            
            place_text = self.small_font.render(f"🏆 #{self.current_season.get('player_place', 42)}", True, GREEN)
            self.screen.blit(place_text, (250, 125))
            
            y_start = 170
        else:
            info_text = self.small_font.render(f"Ваш ID: {self.player_id}", True, WHITE)
            info_rect = info_text.get_rect(center=(SCREEN_WIDTH//2, 110))
            self.screen.blit(info_text, info_rect)
            y_start = 140
        
        for button in self.buttons:
            button.rect.y = y_start
            button.update(mouse_pos, mouse_clicked)
            button.draw(self.screen, self.font)
            y_start += 50
    
    def draw_profile(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("ПРОФИЛЬ", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 40))
        self.screen.blit(title, title_rect)
        
        avatar = Avatar(140, 70, 80)
        avatar.draw(self.screen, self.user.get('donor_frame', 'none'))
        
        y_start = 170
        
        id_text = self.small_font.render("ID:", True, WHITE)
        self.screen.blit(id_text, (30, y_start))
        id_value = self.font.render(self.user['id'], True, GOLD)
        self.screen.blit(id_value, (100, y_start))
        
        y_start += 35
        nick_text = self.small_font.render("Ник:", True, WHITE)
        self.screen.blit(nick_text, (30, y_start))
        nick_value = self.font.render(self.user['username'], True, WHITE)
        self.screen.blit(nick_value, (100, y_start))
        
        edit_nick_rect = pygame.Rect(250, y_start-5, 80, 30)
        hovered = edit_nick_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            edit_color = (0,0,150)
        elif hovered:
            edit_color = (100,100,255)
        else:
            edit_color = BLUE
        
        pygame.draw.rect(self.screen, edit_color, edit_nick_rect, border_radius=5)
        edit_text = self.small_font.render("✏️", True, WHITE)
        edit_text_rect = edit_text.get_rect(center=edit_nick_rect.center)
        self.screen.blit(edit_text, edit_text_rect)
        
        y_start += 40
        stats_title = self.small_font.render("Статистика:", True, WHITE)
        self.screen.blit(stats_title, (30, y_start))
        
        stats = [
            f"💰 Монеты: {self.user['coins']}",
            f"⭐ Рейтинг: {self.user['rating']}",
            f"🏆 Побед: {self.user['wins']}",
            f"📉 Поражений: {self.user['losses']}"
        ]
        
        y_start += 25
        for stat in stats:
            stat_text = self.font.render(stat, True, WHITE)
            self.screen.blit(stat_text, (50, y_start))
            y_start += 25
        
        if self.user.get('donor_tier') and self.user['donor_tier'] != 'none':
            tier_names = {'supporter': '🌟 Сторонник', 'booster': '⚡ Бустер', 'sponsor': '👑 Спонсор'}
            tier_text = self.font.render(tier_names.get(self.user['donor_tier'], self.user['donor_tier']), True, GOLD)
            self.screen.blit(tier_text, (30, y_start))
    
    def draw_edit_nickname(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("СМЕНА НИКА", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 50))
        self.screen.blit(title, title_rect)
        
        current_text = self.small_font.render(f"Текущий ник: {self.user['username']}", True, WHITE)
        current_rect = current_text.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(current_text, current_rect)
        
        input_label = self.small_font.render("Новый ник:", True, WHITE)
        self.screen.blit(input_label, (50, 150))
        
        input_rect = pygame.Rect(50, 180, 260, 40)
        pygame.draw.rect(self.screen, WHITE, input_rect)
        pygame.draw.rect(self.screen, GREEN, input_rect, 3)
        
        input_text = self.font.render(self.keyboard.current_input if self.keyboard.current_input else "введите ник", True, BLACK if self.keyboard.current_input else GRAY)
        self.screen.blit(input_text, (55, 190))
        
        self.keyboard.draw(self.screen, self.font, mouse_pos, mouse_clicked)
    
    def draw_online_menu(self, mouse_pos, mouse_clicked):
        title = self.big_font.render("🌐 ОНЛАЙН ИГРА", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 30))
        self.screen.blit(title, title_rect)
        
        if self.user:
            user_rect = pygame.Rect(20, 50, SCREEN_WIDTH-40, 50)
            pygame.draw.rect(self.screen, (255,255,255,160), user_rect, border_radius=5)
            name_text = self.font.render(f"{self.user['username']}", True, BLACK)
            self.screen.blit(name_text, (30, 60))
            balance_text = self.small_font.render(f"💰 {self.user['coins']}", True, GOLD)
            self.screen.blit(balance_text, (30, 80))
            
            bet_rect = pygame.Rect(20, 110, SCREEN_WIDTH-40, 40)
            pygame.draw.rect(self.screen, (255,255,255,160), bet_rect, border_radius=5)
            bet_text = self.font.render(f"Ставка: {self.bet_amount}", True, GOLD)
            self.screen.blit(bet_text, (30, 120))
        
        y_start = 170
        for button in self.buttons[:5]:
            button.rect.y = y_start
            button.update(mouse_pos, mouse_clicked)
            button.draw(self.screen, self.font)
            y_start += 45
        
        if self.waiting_for_opponent:
            wait_rect = pygame.Rect(20, 400, SCREEN_WIDTH-40, 40)
            pygame.draw.rect(self.screen, (255,255,255,160), wait_rect, border_radius=5)
            wait_text = self.font.render("⏳ Ожидание...", True, BLUE)
            wait_rect = wait_text.get_rect(center=(SCREEN_WIDTH//2, 420))
            self.screen.blit(wait_text, wait_rect)
            if self.room_id:
                room_text = self.small_font.render(f"ID: {self.room_id}", True, PURPLE)
                room_rect = room_text.get_rect(center=(SCREEN_WIDTH//2, 460))
                self.screen.blit(room_text, room_rect)
        
        self.buttons[5].rect.y = 590
        self.buttons[5].update(mouse_pos, mouse_clicked)
        self.buttons[5].draw(self.screen, self.font)
    
    def draw_join_room(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("ВОЙТИ В КОМНАТУ", True, PURPLE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 50))
        self.screen.blit(title, title_rect)
        
        pygame.draw.rect(self.screen, WHITE, (50, 150, 260, 40))
        pygame.draw.rect(self.screen, GREEN, (50, 150, 260, 40), 2)
        id_label = self.small_font.render("ID комнаты:", True, WHITE)
        self.screen.blit(id_label, (50, 130))
        id_text = self.font.render(self.keyboard.current_input if self.keyboard.current_input else "введите ID", True, BLACK if self.keyboard.current_input else GRAY)
        self.screen.blit(id_text, (55, 160))
        
        self.keyboard.draw(self.screen, self.font, mouse_pos, mouse_clicked)
    
    def draw_game(self, title_text, mouse_pos, mouse_clicked):
        title = self.small_font.render(title_text, True, WHITE)
        self.screen.blit(title, (10, 5))
        
        if self.state == "online_game":
            turn_text = self.small_font.render(
                f"{'Твой ход' if self.is_my_turn else 'Ход противника'}",
                True, GREEN if self.is_my_turn else RED
            )
            self.screen.blit(turn_text, (200, 5))
        
        self.game.draw(self.screen, 0, 20)
        
        back_rect = pygame.Rect(280, 580, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (290, 585))
        
        if self.game.game_over:
            winner = "X" if self.game.winner == 1 else "O"
            over_text = self.big_font.render(f"Победил {winner}!", True, GOLD)
            over_rect = over_text.get_rect(center=(SCREEN_WIDTH//2, 300))
            self.screen.blit(over_text, over_rect)
    
    def draw_hall_of_fame(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("🏆 АЛЛЕЯ СЛАВЫ", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 40))
        self.screen.blit(title, title_rect)
        
        y_start = 70
        for season in self.hall_of_fame:
            season_rect = pygame.Rect(20, y_start, SCREEN_WIDTH-40, 70)
            pygame.draw.rect(self.screen, (255,255,255,180), season_rect, border_radius=8)
            pygame.draw.rect(self.screen, GOLD, season_rect, 2, border_radius=8)
            
            season_text = self.font.render(f"Сезон {season['season']}", True, GOLD)
            self.screen.blit(season_text, (30, y_start + 5))
            
            winner_text = self.small_font.render(f"👑 {season['winner']} - {season['rating']}⭐", True, BLACK)
            self.screen.blit(winner_text, (30, y_start + 30))
            
            if season.get('comment'):
                comment_text = self.small_font.render(f"💬 {season['comment'][:30]}", True, GRAY)
                self.screen.blit(comment_text, (30, y_start + 50))
            
            y_start += 80
            if y_start > SCREEN_HEIGHT - 50:
                break
    
    def draw_social_menu(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("👥 СОЦИАЛЬНОЕ", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 40))
        self.screen.blit(title, title_rect)
        
        stats_rect = pygame.Rect(20, 70, SCREEN_WIDTH-40, 60)
        pygame.draw.rect(self.screen, (255,255,255,160), stats_rect, border_radius=10)
        
        friends_online = self.small_font.render("Друзья онлайн: 3", True, BLACK)
        self.screen.blit(friends_online, (30, 80))
        
        unread_text = self.small_font.render("Непрочитанных: 5", True, BLACK)
        self.screen.blit(unread_text, (30, 105))
        
        y_start = 150
        for button in self.buttons:
            button.rect.y = y_start
            button.update(mouse_pos, mouse_clicked)
            button.draw(self.screen, self.font)
            y_start += 50
    
    def draw_friends(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("👥 ДРУЗЬЯ", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 40))
        self.screen.blit(title, title_rect)
        
        search_rect = pygame.Rect(30, 70, 260, 30)
        pygame.draw.rect(self.screen, WHITE, search_rect)
        pygame.draw.rect(self.screen, BLUE, search_rect, 2)
        search_text = self.small_font.render("🔍 Поиск по имени...", True, GRAY)
        self.screen.blit(search_text, (35, 75))
        
        y_start = 120
        friends = [
            {"name": "Player_K7F9", "online": True, "status": "В игре"},
            {"name": "Champion_X", "online": True, "status": "Онлайн"},
            {"name": "SuperStar", "online": False, "status": "Был 2ч назад"},
        ]
        
        for friend in friends:
            friend_rect = pygame.Rect(20, y_start, SCREEN_WIDTH-40, 50)
            pygame.draw.rect(self.screen, (255,255,255,160), friend_rect, border_radius=8)
            
            status_color = GREEN if friend['online'] else GRAY
            pygame.draw.circle(self.screen, status_color, (35, y_start + 15), 5)
            
            name_text = self.font.render(friend['name'], True, BLACK)
            self.screen.blit(name_text, (45, y_start + 5))
            
            status_text = self.small_font.render(friend['status'], True, GRAY)
            self.screen.blit(status_text, (45, y_start + 25))
            
            chat_btn = pygame.Rect(250, y_start + 10, 50, 30)
            hovered = chat_btn.collidepoint(mouse_pos)
            pressed = hovered and mouse_clicked
            
            if pressed:
                btn_color = (0,0,150)
            elif hovered:
                btn_color = (100,100,255)
            else:
                btn_color = BLUE
            
            pygame.draw.rect(self.screen, btn_color, chat_btn, border_radius=5)
            chat_text = self.small_font.render("Чат", True, WHITE)
            chat_rect = chat_text.get_rect(center=chat_btn.center)
            self.screen.blit(chat_text, chat_rect)
            
            y_start += 60
            if y_start > SCREEN_HEIGHT - 50:
                break
    
    def draw_chats(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("💬 ЧАТЫ", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 40))
        self.screen.blit(title, title_rect)
        
        y_start = 80
        chats = [
            {"name": "Player_K7F9", "last": "Привет! Сыграем?", "time": "5 мин", "unread": 2},
            {"name": "Champion_X", "last": "Поздравляю с победой!", "time": "1 час", "unread": 0},
            {"name": "Команда", "last": "Новый турнир!", "time": "2 часа", "unread": 5},
        ]
        
        for chat in chats:
            chat_rect = pygame.Rect(20, y_start, SCREEN_WIDTH-40, 60)
            pygame.draw.rect(self.screen, (255,255,255,160), chat_rect, border_radius=8)
            
            name_text = self.font.render(chat['name'], True, BLACK)
            self.screen.blit(name_text, (30, y_start + 5))
            
            last_text = self.small_font.render(chat['last'], True, GRAY)
            self.screen.blit(last_text, (30, y_start + 25))
            
            time_text = self.small_font.render(chat['time'], True, GRAY)
            self.screen.blit(time_text, (250, y_start + 5))
            
            if chat['unread'] > 0:
                unread_rect = pygame.Rect(300, y_start + 25, 20, 20)
                pygame.draw.circle(self.screen, RED, unread_rect.center, 10)
                unread_text = self.small_font.render(str(chat['unread']), True, WHITE)
                unread_rect = unread_text.get_rect(center=unread_rect.center)
                self.screen.blit(unread_text, unread_rect)
            
            y_start += 70
            if y_start > SCREEN_HEIGHT - 50:
                break
    
    def draw_notifications(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("🔔 УВЕДОМЛЕНИЯ", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 40))
        self.screen.blit(title, title_rect)
        
        y_start = 80
        notifications = [
            {"title": "Заявка в друзья", "text": "Player_K7F9 хочет добавить вас в друзья", "time": "5 мин"},
            {"title": "Приглашение в игру", "text": "Champion_X приглашает сыграть (ставка 100💰)", "time": "1 час"},
            {"title": "Турнир", "text": "Турнир начнется через 1 час", "time": "2 часа"},
        ]
        
        for notif in notifications:
            notif_rect = pygame.Rect(20, y_start, SCREEN_WIDTH-40, 60)
            pygame.draw.rect(self.screen, (255,255,255,160), notif_rect, border_radius=8)
            
            title_text = self.font.render(notif['title'], True, GOLD)
            self.screen.blit(title_text, (30, y_start + 5))
            
            msg_text = self.small_font.render(notif['text'], True, BLACK)
            self.screen.blit(msg_text, (30, y_start + 30))
            
            time_text = self.small_font.render(notif['time'], True, GRAY)
            self.screen.blit(time_text, (250, y_start + 35))
            
            y_start += 70
            if y_start > SCREEN_HEIGHT - 50:
                break
    
    def draw_achievements(self, mouse_pos, mouse_clicked):
        back_rect = pygame.Rect(10, 10, 70, 30)
        hovered = back_rect.collidepoint(mouse_pos)
        pressed = hovered and mouse_clicked
        
        if pressed:
            back_color = (150,0,0)
        elif hovered:
            back_color = (255,100,100)
        else:
            back_color = RED
        
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=5)
        back_text = self.small_font.render("Назад", True, WHITE)
        self.screen.blit(back_text, (20, 15))
        
        title = self.big_font.render("🏆 ДОСТИЖЕНИЯ", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 40))
        self.screen.blit(title, title_rect)
        
        stats_rect = pygame.Rect(20, 60, SCREEN_WIDTH-40, 40)
        pygame.draw.rect(self.screen, (255,255,255,160), stats_rect, border_radius=8)
        
        stats_text = self.small_font.render("⭐ Прогресс: 12/45 | 🏆 Очки: 120", True, BLACK)
        stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.screen.blit(stats_text, stats_rect)
        
        categories = [
            {"name": "🏆 Победные", "color": GOLD, "achievements": [
                {"name": "Первая победа", "progress": "1/1", "completed": True},
                {"name": "10 побед", "progress": "7/10", "completed": False},
                {"name": "50 побед", "progress": "7/50", "completed": False}
            ]},
            {"name": "👥 Социальные", "color": BLUE, "achievements": [
                {"name": "Первый друг", "progress": "1/1", "completed": True},
                {"name": "5 друзей", "progress": "3/5", "completed": False}
            ]}
        ]
        
        y_start = 110
        for cat in categories:
            if y_start > SCREEN_HEIGHT - 150:
                break
                
            cat_text = self.font.render(cat["name"], True, cat["color"])
            self.screen.blit(cat_text, (20, y_start))
            y_start += 25
            
            for ach in cat["achievements"]:
                ach_rect = pygame.Rect(30, y_start, SCREEN_WIDTH-60, 25)
                
                if ach["completed"]:
                    color = (200,255,200)
                    border = GREEN
                else:
                    color = (255,255,255,160)
                    border = GRAY
                    
                pygame.draw.rect(self.screen, color, ach_rect, border_radius=4)
                pygame.draw.rect(self.screen, border, ach_rect, 1, border_radius=4)
                
                name_text = self.small_font.render(ach["name"], True, BLACK)
                self.screen.blit(name_text, (35, y_start + 5))
                
                prog_text = self.small_font.render(ach["progress"], True, GRAY)
                self.screen.blit(prog_text, (270, y_start + 5))
                
                y_start += 28
                if y_start > SCREEN_HEIGHT - 80:
                    break
            
            y_start += 10
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.draw()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()