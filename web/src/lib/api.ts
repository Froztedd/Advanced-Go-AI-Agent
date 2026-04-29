import type { AgentInfo, GameState, NewGameRequest } from './types'

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? 'http://localhost:8000'

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // ignore
    }
    throw new Error(`${res.status}: ${detail}`)
  }
  return (await res.json()) as T
}

export const api = {
  listAgents: () => jsonFetch<AgentInfo[]>('/agents'),
  createGame: (req: NewGameRequest) =>
    jsonFetch<GameState>('/games', { method: 'POST', body: JSON.stringify(req) }),
  getGame: (id: string) => jsonFetch<GameState>(`/games/${id}`),
  makeMove: (id: string, move: string) =>
    jsonFetch<GameState>(`/games/${id}/move`, {
      method: 'POST',
      body: JSON.stringify({ move }),
    }),
  resign: (id: string) =>
    jsonFetch<GameState>(`/games/${id}/resign`, { method: 'POST' }),
}
