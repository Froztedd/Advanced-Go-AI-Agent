export type ColorName = 'black' | 'white' | 'empty'
export type GameStatus = 'in_progress' | 'finished' | 'resigned'

export interface AgentInfo {
  name: string
  label: string
  description: string
  strength: number
}

export interface MoveRecord {
  color: ColorName
  move: string
  by: 'human' | 'agent'
  elapsed_ms: number
}

export interface ScoreInfo {
  black: number
  white: number
  winner: ColorName
}

export interface GameState {
  game_id: string
  status: GameStatus
  human_color: ColorName
  agent_color: ColorName
  agent_name: string
  time_limit: number
  board_size: number
  cells: number[][]
  move_number: number
  consecutive_passes: number
  color_to_play: ColorName
  legal_moves: string[]
  last_move: string | null
  moves: MoveRecord[]
  captures: { black: number; white: number; empty: number }
  score: ScoreInfo | null
  agent_thinking: boolean
}

export interface NewGameRequest {
  human_color: ColorName
  agent: string
  time_limit: number
  board_size: number
}
