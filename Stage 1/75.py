import sys
import time
from read import readInput
from write import writeOutput
from host import GO

# Helper methods for GO class
def detect_neighbor_empty(self, i, j):
    neighbors = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for d in directions:
        ni, nj = i + d[0], j + d[1]
        if 0 <= ni < self.size and 0 <= nj < self.size:
            if self.board[ni][nj] == 0:
                neighbors.append((ni, nj))
    return neighbors

def detect_neighbor_ally(self, i, j, stone_color=None):
    if stone_color is None:
        stone_color = self.board[i][j]
    neighbors = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for d in directions:
        ni, nj = i + d[0], j + d[1]
        if 0 <= ni < self.size and 0 <= nj < self.size:
            if self.board[ni][nj] == stone_color:
                neighbors.append((ni, nj))
    return neighbors

def detect_liberties(self, i, j):
    visited = set()
    to_visit = [(i, j)]
    liberties = set()
    stone_color = self.board[i][j]

    while to_visit:
        x, y = to_visit.pop()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        neighbors = [
            (x + dx, y + dy)
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]
            if 0 <= x + dx < self.size and 0 <= y + dy < self.size
        ]
        for nx, ny in neighbors:
            if self.board[nx][ny] == 0:
                liberties.add((nx, ny))
            elif self.board[nx][ny] == stone_color and (nx, ny) not in visited:
                to_visit.append((nx, ny))
    return liberties

# Attach methods to GO class
GO.detect_neighbor_empty = detect_neighbor_empty
GO.detect_neighbor_ally = detect_neighbor_ally
GO.detect_liberties = detect_liberties

class AdvancedGoAgent:
    def __init__(self):
        self.max_depth = 4
        self.time_limit = 9.5
        self.start_time = None
        self.board_size = 5
        self.weights = {
            'liberty': 4.0,
            'connection': 3.0,
            'territory': 2.5,
            'capture': 5.0,
            'center': 2.5,
            'edge': 1.5,
            'corner': 1.0
        }

    def get_move(self, go_state, stone_color):
        self.start_time = time.time()
        opp_color = 3 - stone_color

        # Use a refined early game strategy
        total_stones = sum(row.count(1) + row.count(2) for row in go_state.board)
        if total_stones < 6:
            move = self.get_early_game_move(go_state, stone_color, total_stones)
            if move:
                return move

        # Initialize search with iterative deepening
        best_move = None
        alpha = float('-inf')
        beta = float('inf')

        # Get moves sorted by heuristic values
        moves = self.get_sorted_moves(go_state, stone_color)
        if not moves:
            return "PASS"

        for depth in range(1, self.max_depth + 1):
            if self.is_time_up():
                break
            for move in moves:
                if self.is_time_up():
                    break
                new_state = go_state.copy_board()
                new_state.place_chess(move[0], move[1], stone_color)
                new_state.remove_died_pieces(opp_color)
                score = -self.negamax(new_state, depth - 1, opp_color, -beta, -alpha)

                if score > alpha:
                    alpha = score
                    best_move = move

        return best_move if best_move else "PASS"

    def get_early_game_move(self, state, stone_color, total_stones):
        center = self.board_size // 2

        if total_stones == 0:
            return (center, center)  # Start at center

        # Early responses based on opponent's positioning
        priority_moves = [
            (center, center),
            (center - 1, center - 1), (center - 1, center + 1),
            (center + 1, center - 1), (center + 1, center + 1),
            (0, 0), (0, 4), (4, 0), (4, 4)
        ]

        for move in priority_moves:
            if state.board[move[0]][move[1]] == 0 and state.valid_place_check(move[0], move[1], stone_color, test_check=True):
                return move

        return None

    def get_sorted_moves(self, state, stone_color):
        moves = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if state.board[i][j] == 0 and state.valid_place_check(i, j, stone_color, test_check=True):
                    score = self.evaluate_move(state, i, j, stone_color)
                    moves.append(((i, j), score))

        moves.sort(key=lambda x: x[1], reverse=True)
        return [move[0] for move in moves[:10]]  # Consider top 10 moves

    def evaluate_move(self, state, i, j, stone_color):
        score = 0
        center = self.board_size // 2

        # Simulate placing the stone
        temp_state = state.copy_board()
        temp_state.place_chess(i, j, stone_color)

        # Capture potential and liberties
        captures = len(temp_state.remove_died_pieces(3 - stone_color))
        liberties = len(temp_state.detect_liberties(i, j))
        score += captures * self.weights['capture']
        score += liberties * self.weights['liberty']

        # Positional evaluation
        dist_to_center = abs(i - center) + abs(j - center)
        score += self.weights['center'] / (dist_to_center + 1)

        # Connection evaluation
        allies = len(state.detect_neighbor_ally(i, j, stone_color))
        score += allies * self.weights['connection']

        return score

    def negamax(self, state, depth, stone_color, alpha, beta):
        if self.is_time_up() or depth == 0:
            return self.evaluate_board(state, stone_color)

        best_score = float('-inf')
        moves = self.get_sorted_moves(state, stone_color)

        for move in moves:
            new_state = state.copy_board()
            new_state.place_chess(move[0], move[1], stone_color)
            new_state.remove_died_pieces(3 - stone_color)

            score = -self.negamax(new_state, depth - 1, 3 - stone_color, -beta, -alpha)
            best_score = max(best_score, score)
            alpha = max(alpha, score)

            if alpha >= beta:
                break

        return best_score

    def evaluate_board(self, state, stone_color):
        score = 0
        opp_color = 3 - stone_color
        center = self.board_size // 2

        # Evaluate positions of stones and territories
        for i in range(self.board_size):
            for j in range(self.board_size):
                if state.board[i][j] == stone_color:
                    score += 10  # Stone value
                    dist_to_center = abs(i - center) + abs(j - center)
                    score += self.weights['center'] / (dist_to_center + 1)
                elif state.board[i][j] == opp_color:
                    score -= 10

        return score

    def is_time_up(self):
        return time.time() - self.start_time > self.time_limit - 0.1

if __name__ == "__main__":
    N = 5
    piece_type, previous_board, board = readInput(N)
    go = GO(N)
    go.set_board(piece_type, previous_board, board)
    player = AdvancedGoAgent()
    action = player.get_move(go, piece_type)
    writeOutput(action) 