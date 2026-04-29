import sys
import time
from read import readInput
from write import writeOutput
from host import GO

class AdvancedGoAgent:
    def __init__(self):
        self.max_depth = 3  # Reduced for stability
        self.time_limit = 9.5
        self.start_time = None
        self.board_size = 5
        self.step_number = 0
        self.previous_state = None

        # Phase-specific weights for more stable performance
        self.opening_weights = {
            'capture': 9.0,
            'liberty': 7.0,
            'territory': 5.0,
            'center': 6.0,
            'connection': 5.0,
            'shape': 4.0
        }

        self.midgame_weights = {
            'capture': 8.0,
            'liberty': 6.0,
            'territory': 6.0,
            'center': 4.0,
            'connection': 6.0,
            'shape': 5.0
        }

        self.endgame_weights = {
            'capture': 7.0,
            'liberty': 5.0,
            'territory': 7.0,
            'center': 3.0,
            'connection': 4.0,
            'shape': 3.0
        }

        self.weights = self.opening_weights

        # Critical patterns for shape analysis
        self.good_patterns = [
            [(0,0), (0,1), (1,0)],  # L-shape
            [(0,0), (1,1)],         # Diagonal
            [(0,0), (0,1), (1,1)]   # Triangle
        ]

    def get_move(self, go_state, stone_color):
        self.start_time = time.time()

        # Update game phase
        total_stones = sum(row.count(1) + row.count(2) for row in go_state.board)
        self.step_number = total_stones
        self.update_weights()

        # Opening game strategy
        if total_stones <= 4:
            move = self.handle_opening(go_state, stone_color)
            if move:
                return move

        moves = self.get_sorted_moves(go_state, stone_color)
        if not moves:
            return "PASS"

        best_move = moves[0][1]  # Access the move from the tuple
        best_score = moves[0][0]  # Access the score from the tuple
        alpha = float('-inf')
        beta = float('inf')

        # Iterative deepening with dynamic depth
        max_depth = min(self.max_depth, 24 - total_stones)

        for depth in range(1, max_depth + 1):
            if self.is_time_up():
                break

            current_best = None
            current_score = float('-inf')

            for score, move, _ in moves[:min(6, len(moves))]:  # Unpack all three elements
                if self.is_time_up():
                    break

                new_state = go_state.copy_board()
                new_state.place_chess(move[0], move[1], stone_color)
                new_state.remove_died_pieces(3 - stone_color)

                eval_score = -self.negamax(new_state, depth - 1, 3 - stone_color, -beta, -alpha)

                if eval_score > current_score or (eval_score == current_score and self.move_heuristic(move) > self.move_heuristic(current_best)):
                    current_score = eval_score
                    current_best = move
                    alpha = max(alpha, eval_score)

            if current_best and not self.is_time_up():
                if current_score > best_score or (current_score == best_score and self.move_heuristic(current_best) > self.move_heuristic(best_move)):
                    best_score = current_score
                    best_move = current_best

        return best_move

    def get_sorted_moves(self, state, stone_color):
        moves = []
        opp_color = 3 - stone_color

        for i in range(self.board_size):
            for j in range(self.board_size):
                if state.board[i][j] == 0 and state.valid_place_check(i, j, stone_color, test_check=True):
                    # Simulate move
                    temp_state = state.copy_board()
                    temp_state.place_chess(i, j, stone_color)

                    # Calculate move priority and score
                    priority = self.get_move_priority(state, temp_state, i, j, stone_color)
                    score = self.evaluate_move(state, i, j, stone_color)

                    # Append a tuple of (score, move, priority)
                    moves.append((score, (i, j), priority))

        # Sort by score first, then by priority, then by move heuristic
        moves.sort(key=lambda x: (-x[0], -x[2], -self.move_heuristic(x[1])))
        return moves[:8]  # Return top 8 moves with their scores and priorities

    def get_move_priority(self, state, temp_state, i, j, stone_color):
        priority = 0
        opp_color = 3 - stone_color

        # Capturing moves get higher priority
        if len(temp_state.remove_died_pieces(opp_color)) > 0:
            priority += 3
        # Urgent defensive moves
        if self.is_urgent_defensive_move(state, i, j, stone_color):
            priority += 2
        # Good shape forming moves
        if self.forms_good_shape(temp_state, i, j, stone_color):
            priority += 1

        return priority

    def move_heuristic(self, move):
        if move is None:
            return -1
        # Heuristic based on distance to center (prefer center moves)
        i, j = move
        center_dist = abs(i - 2) + abs(j - 2)
        return -center_dist  # Negative because we sort in descending order

    def is_urgent_defensive_move(self, state, i, j, stone_color):
        temp_state = state.copy_board()
        temp_state.place_chess(i, j, stone_color)

        for di, dj in [(-1,0), (0,-1), (0,1), (1,0)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < self.board_size and 0 <= nj < self.board_size:
                if state.board[ni][nj] == stone_color:
                    if len(self.find_liberties(state, ni, nj)) <= 2:
                        return True
        return False

    def forms_good_shape(self, state, i, j, stone_color):
        for pattern in self.good_patterns:
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    matches = True
                    for px, py in pattern:
                        x, y = i + px + di, j + py + dj
                        if not (0 <= x < self.board_size and 0 <= y < self.board_size and
                                state.board[x][y] == stone_color):
                            matches = False
                            break
                    if matches:
                        return True
        return False

    def evaluate_move(self, state, i, j, stone_color):
        score = 0
        temp_state = state.copy_board()
        temp_state.place_chess(i, j, stone_color)
        opp_color = 3 - stone_color

        # Capture value
        captures = len(temp_state.remove_died_pieces(opp_color))
        score += captures * self.weights['capture']

        # Liberty analysis
        liberty_count = len(self.find_liberties(temp_state, i, j))
        score += liberty_count * self.weights['liberty']

        # Territory control
        territory_score = self.evaluate_territory(temp_state, i, j, stone_color)
        score += territory_score * self.weights['territory']

        # Position value
        score += self.evaluate_position(i, j) * self.weights['center']

        # Connection value
        allies = len(state.detect_neighbor_ally(i, j))
        score += allies * self.weights['connection']

        # Shape value
        if self.forms_good_shape(temp_state, i, j, stone_color):
            score += self.weights['shape']

        return score

    def find_liberties(self, state, i, j):
        color = state.board[i][j]
        visited = set()
        liberties = set()
        stack = [(i, j)]

        while stack:
            x, y = stack.pop()
            if (x, y) not in visited:
                visited.add((x, y))
                for dx, dy in [(-1,0), (0,-1), (0,1), (1,0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                        if state.board[nx][ny] == 0:
                            liberties.add((nx, ny))
                        elif state.board[nx][ny] == color and (nx, ny) not in visited:
                            stack.append((nx, ny))
        return liberties

    def evaluate_territory(self, state, i, j, stone_color):
        score = 0
        visited = set()
        queue = [(i, j)]

        while queue:
            x, y = queue.pop(0)
            if (x, y) in visited:
                continue

            visited.add((x, y))
            for dx, dy in [(-1,0), (0,-1), (0,1), (1,0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size and (nx, ny) not in visited:
                    if state.board[nx][ny] == 0:
                        score += 0.5
                        queue.append((nx, ny))
                    elif state.board[nx][ny] == stone_color:
                        score += 1
                        queue.append((nx, ny))
                    else:
                        score -= 0.5

        return score

    def evaluate_position(self, i, j):
        center_dist = abs(i - 2) + abs(j - 2)
        if center_dist == 0:
            return 3.0
        elif center_dist == 1:
            return 2.0
        elif center_dist == 2:
            return 1.0
        return 0.0

    def handle_opening(self, state, stone_color):
        if self.step_number == 0:
            return (2, 2)

        if state.board[2][2] == 3 - stone_color:
            corners = [(0,0), (0,4), (4,0), (4,4)]
            for corner in corners:
                if state.valid_place_check(corner[0], corner[1], stone_color, test_check=True):
                    return corner

        strategic_points = [
            (2,2), (1,1), (1,3), (3,1), (3,3),
            (0,2), (2,0), (2,4), (4,2)
        ]

        for point in strategic_points:
            if state.valid_place_check(point[0], point[1], stone_color, test_check=True):
                return point

        return None

    def update_weights(self):
        if self.step_number < 8:
            self.weights = self.opening_weights
        elif self.step_number < 16:
            self.weights = self.midgame_weights
        else:
            self.weights = self.endgame_weights

    def negamax(self, state, depth, stone_color, alpha, beta):
        if depth == 0 or self.is_time_up():
            return self.evaluate_board(state, stone_color)

        moves = self.get_sorted_moves(state, stone_color)
        if not moves:
            return 0

        best_score = float('-inf')
        for score, move, _ in moves[:5]:  # Unpack all three elements
            if self.is_time_up():
                break

            new_state = state.copy_board()
            new_state.place_chess(move[0], move[1], stone_color)
            new_state.remove_died_pieces(3 - stone_color)

            eval_score = -self.negamax(new_state, depth - 1, 3 - stone_color, -beta, -alpha)

            if eval_score > best_score:
                best_score = eval_score
            alpha = max(alpha, eval_score)

            if alpha >= beta:
                break

        return best_score

    def evaluate_board(self, state, stone_color):
        score = 0
        opp_color = 3 - stone_color

        for i in range(self.board_size):
            for j in range(self.board_size):
                if state.board[i][j] == stone_color:
                    score += 10
                    score += len(self.find_liberties(state, i, j))
                elif state.board[i][j] == opp_color:
                    score -= 10
                    score -= len(self.find_liberties(state, i, j))

        return score

    def is_time_up(self):
        return time.time() - self.start_time > self.time_limit - 0.1

def main():
    N = 5
    piece_type, previous_board, board = readInput(N)
    go = GO(N)
    go.set_board(piece_type, previous_board, board)
    player = AdvancedGoAgent()
    action = player.get_move(go, piece_type)
    writeOutput(action)

if __name__ == "__main__":
    main()
