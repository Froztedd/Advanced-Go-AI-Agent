# Advanced Go AI Agent

An AI agent for playing the game of Go (5x5 board) using heuristic evaluation and minimax search with alpha-beta pruning.

## Overview

This project implements an AI for the game of Go using a negamax algorithm (variation of minimax) with alpha-beta pruning. The agent uses a combination of heuristic evaluation metrics to determine optimal moves, including:

- Liberty count (open adjacent points)
- Capture potential
- Stone connections
- Territory control
- Board position (center vs edge vs corner positioning)

The implementation includes specialized logic for the opening game (first few moves) and a time-controlled search to ensure moves are made within the allocated time limit.

## Features

- **Negamax search with alpha-beta pruning**: For efficient search of the game tree
- **Iterative deepening**: To handle time constraints effectively
- **Heuristic evaluation**: Comprehensive board evaluation using multiple weighted factors
- **Early game strategy**: Special logic for opening moves
- **Move sorting**: Optimization to improve alpha-beta pruning efficiency
- **Liberty detection**: Accurate tracking of stone liberties for tactical decisions

## Code Structure

The code is organized into three main components:

1. **GO class extensions**: Additional helper methods for the GO class to detect liberties, allies, and empty spaces
2. **AdvancedGoAgent class**: Main AI implementation with:
   - Move selection logic
   - Board evaluation
   - Search algorithm implementation
   - Early game strategies

## How It Works

The agent works as follows:

1. **Initialization**: Set up the agent with configuration parameters including search depth and evaluation weights
2. **Move Selection**:
   - For early game (first 6 moves), use predefined opening strategies
   - For mid/late game, use negamax search with iterative deepening
3. **Move Evaluation**:
   - Generates possible moves and sorts them by heuristic value
   - Performs alpha-beta search to the specified depth (or until time runs out)
   - Returns the best move found or "PASS" if no good moves are available

The evaluation function considers:
- Number of stones of each color
- Liberty count for stone groups
- Captures and capture potential
- Board position (center control vs edges)
- Stone connections

## Usage

The agent can be used in a Go game framework that provides the board state and expects a move in return:

```python
from go_agent import AdvancedGoAgent

# Initialize the game state
go = GO(5)  # 5x5 board
go.set_board(piece_type, previous_board, board)

# Create the agent
player = AdvancedGoAgent()

# Get the best move
action = player.get_move(go, piece_type)
```

The agent interfaces with the game through:
- `readInput()`: Reads the current game state
- `writeOutput()`: Returns the selected move

## Parameters

The agent behavior can be tuned by adjusting:

- `max_depth`: Maximum search depth (default: 4)
- `time_limit`: Maximum thinking time in seconds (default: 9.5)
- Evaluation weights in the `weights` dictionary:
  - `liberty`: Value of each liberty point
  - `connection`: Value of connected stones
  - `territory`: Value of controlled territory
  - `capture`: Value of capturing opponent stones
  - `center`: Value of controlling center positions
  - `edge`: Value of edge positions
  - `corner`: Value of corner positions

## Requirements

- Python 3.x
- Go game implementation with the expected interface (`GO` class)

## Future Improvements

Potential enhancements include:
- Machine learning for parameter tuning
- Pattern recognition for common Go situations
- Endgame optimization
- Transposition tables for search efficiency
- Support for larger board sizes