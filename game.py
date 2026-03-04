import pygame
import json

# Константы
CELL_SIZE = 35
LINE_WIDTH = 3
BOARD_SIZE = CELL_SIZE * 9

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)
GREEN = (0, 255, 0)

class SuperTicTacToe:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.boards = [[0] * 9 for _ in range(9)]
        self.section_winners = [0] * 9
        self.current_player = 1
        self.active_section = -1
        self.game_over = False
        self.winner = 0
        self.move_history = []
    
    def get_section_index(self, row, col):
        return (row // 3) * 3 + (col // 3)
    
    def get_cell_index(self, row, col):
        return (row % 3) * 3 + (col % 3)
    
    def get_global_coords(self, section, cell):
        section_row = section // 3
        section_col = section % 3
        cell_row = cell // 3
        cell_col = cell % 3
        
        return (
            section_row * 3 + cell_row,
            section_col * 3 + cell_col
        )
    
    def check_section(self, section):
        board = [self.boards[section][i] for i in range(9)]
        
        wins = [
            [0,1,2], [3,4,5], [6,7,8],
            [0,3,6], [1,4,7], [2,5,8],
            [0,4,8], [2,4,6]
        ]
        
        for combo in wins:
            if board[combo[0]] != 0 and \
               board[combo[0]] == board[combo[1]] == board[combo[2]]:
                return board[combo[0]]
        
        if all(cell != 0 for cell in board):
            return 3
        
        return 0
    
    def check_global_winner(self):
        winners = self.section_winners
        
        wins = [
            [0,1,2], [3,4,5], [6,7,8],
            [0,3,6], [1,4,7], [2,5,8],
            [0,4,8], [2,4,6]
        ]
        
        for combo in wins:
            if winners[combo[0]] in [1,2] and \
               winners[combo[0]] == winners[combo[1]] == winners[combo[2]]:
                return winners[combo[0]]
        
        return 0
    
    def make_move(self, row, col):
        if self.game_over:
            return False, "Игра окончена"
        
        if not (0 <= row < 9 and 0 <= col < 9):
            return False, "Вне поля"
        
        section = self.get_section_index(row, col)
        cell = self.get_cell_index(row, col)
        
        if self.active_section != -1 and self.active_section != section:
            return False, "Сейчас нельзя ходить сюда"
        
        if self.section_winners[section] != 0:
            return False, "Эта секция уже закрыта"
        
        if self.boards[section][cell] != 0:
            return False, "Клетка занята"
        
        self.boards[section][cell] = self.current_player
        self.move_history.append({
            'player': self.current_player,
            'section': section,
            'cell': cell,
            'row': row,
            'col': col
        })
        
        winner = self.check_section(section)
        if winner != 0:
            self.section_winners[section] = winner
            
            global_winner = self.check_global_winner()
            if global_winner != 0:
                self.game_over = True
                self.winner = global_winner
                return True, "Победа!"
        
        next_section = cell
        
        if next_section >= 9 or self.section_winners[next_section] != 0:
            self.active_section = -1
        else:
            self.active_section = next_section
        
        self.current_player = 3 - self.current_player
        
        return True, "OK"
    
    def get_state(self):
        return {
            'boards': self.boards,
            'section_winners': self.section_winners,
            'current_player': self.current_player,
            'active_section': self.active_section,
            'game_over': self.game_over,
            'winner': self.winner,
            'move_history': self.move_history
        }
    
    def load_state(self, state):
        self.boards = state['boards']
        self.section_winners = state['section_winners']
        self.current_player = state['current_player']
        self.active_section = state['active_section']
        self.game_over = state['game_over']
        self.winner = state['winner']
        self.move_history = state.get('move_history', [])
    
    def draw(self, screen, offset_x=0, offset_y=0):
        pygame.draw.rect(screen, WHITE, 
                        (offset_x, offset_y, BOARD_SIZE, BOARD_SIZE))
        
        for i in range(1, 3):
            x = offset_x + i * 3 * CELL_SIZE
            pygame.draw.line(screen, BLACK, 
                           (x, offset_y), 
                           (x, offset_y + BOARD_SIZE), 
                           LINE_WIDTH * 3)
            
            y = offset_y + i * 3 * CELL_SIZE
            pygame.draw.line(screen, BLACK, 
                           (offset_x, y), 
                           (offset_x + BOARD_SIZE, y), 
                           LINE_WIDTH * 3)
        
        for i in range(1, 9):
            if i % 3 != 0:
                x = offset_x + i * CELL_SIZE
                pygame.draw.line(screen, GRAY, 
                               (x, offset_y), 
                               (x, offset_y + BOARD_SIZE), 
                               1)
                
                y = offset_y + i * CELL_SIZE
                pygame.draw.line(screen, GRAY, 
                               (offset_x, y), 
                               (offset_x + BOARD_SIZE, y), 
                               1)
        
        if self.active_section != -1 and not self.game_over:
            section_row = self.active_section // 3
            section_col = self.active_section % 3
            x = offset_x + section_col * 3 * CELL_SIZE
            y = offset_y + section_row * 3 * CELL_SIZE
            
            s = pygame.Surface((3*CELL_SIZE, 3*CELL_SIZE), pygame.SRCALPHA)
            s.fill((173, 216, 230, 100))
            screen.blit(s, (x, y))
        
        for section in range(9):
            for cell in range(9):
                if self.boards[section][cell] == 0:
                    continue
                
                row, col = self.get_global_coords(section, cell)
                x = offset_x + col * CELL_SIZE
                y = offset_y + row * CELL_SIZE
                
                if self.boards[section][cell] == 1:
                    self._draw_x(screen, x, y, CELL_SIZE)
                else:
                    self._draw_o(screen, x, y, CELL_SIZE)
        
        for section in range(9):
            if self.section_winners[section] in [1, 2]:
                section_row = section // 3
                section_col = section % 3
                x = offset_x + section_col * 3 * CELL_SIZE
                y = offset_y + section_row * 3 * CELL_SIZE
                
                if self.section_winners[section] == 1:
                    self._draw_large_x(screen, x, y, 3*CELL_SIZE)
                else:
                    self._draw_large_o(screen, x, y, 3*CELL_SIZE)
            
            elif self.section_winners[section] == 3:
                section_row = section // 3
                section_col = section % 3
                x = offset_x + section_col * 3 * CELL_SIZE
                y = offset_y + section_row * 3 * CELL_SIZE
                s = pygame.Surface((3*CELL_SIZE, 3*CELL_SIZE), pygame.SRCALPHA)
                s.fill((200, 200, 200, 150))
                screen.blit(s, (x, y))
    
    def _draw_x(self, screen, x, y, size):
        offset = size // 4
        pygame.draw.line(screen, RED, 
                        (x + offset, y + offset),
                        (x + size - offset, y + size - offset),
                        LINE_WIDTH * 2)
        pygame.draw.line(screen, RED,
                        (x + size - offset, y + offset),
                        (x + offset, y + size - offset),
                        LINE_WIDTH * 2)
    
    def _draw_o(self, screen, x, y, size):
        offset = size // 4
        pygame.draw.circle(screen, BLUE,
                          (x + size//2, y + size//2),
                          size//2 - offset,
                          LINE_WIDTH * 2)
    
    def _draw_large_x(self, screen, x, y, size):
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        offset = size // 4
        pygame.draw.line(s, (255, 0, 0, 200),
                        (offset, offset),
                        (size - offset, size - offset),
                        LINE_WIDTH * 3)
        pygame.draw.line(s, (255, 0, 0, 200),
                        (size - offset, offset),
                        (offset, size - offset),
                        LINE_WIDTH * 3)
        screen.blit(s, (x, y))
    
    def _draw_large_o(self, screen, x, y, size):
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(s, (0, 0, 255, 200),
                          (size//2, size//2),
                          size//2 - size//8,
                          LINE_WIDTH * 3)
        screen.blit(s, (x, y))