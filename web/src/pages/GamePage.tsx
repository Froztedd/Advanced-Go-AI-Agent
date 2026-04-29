import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { gsap } from 'gsap'
import { api } from '../lib/api'
import GameBoard from '../components/GameBoard'
import type { ColorName, GameState } from '../lib/types'

export default function GamePage() {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const gameQ = useQuery({
    queryKey: ['game', gameId],
    queryFn: () => api.getGame(gameId!),
    enabled: !!gameId,
  })

  const moveMut = useMutation({
    mutationFn: (move: string) => api.makeMove(gameId!, move),
    onSuccess: (data) => queryClient.setQueryData(['game', gameId], data),
  })
  const resignMut = useMutation({
    mutationFn: () => api.resign(gameId!),
    onSuccess: (data) => queryClient.setQueryData(['game', gameId], data),
  })

  const state = gameQ.data
  if (!gameId) return <div className="p-8">No game id</div>
  if (gameQ.isLoading) return <div className="p-8 text-ink-300">Loading game…</div>
  if (gameQ.isError) {
    return (
      <div className="p-8 text-red-400">
        Could not load game. {(gameQ.error as Error).message}
      </div>
    )
  }
  if (!state) return null

  const isHumanTurn = state.color_to_play === state.human_color && state.status === 'in_progress'
  const isAgentThinking = moveMut.isPending && state.status === 'in_progress'
  const isOver = state.status !== 'in_progress'

  return (
    <div className="px-4 md:px-6 py-8 max-w-6xl mx-auto w-full">
      <div className="grid lg:grid-cols-[1fr_320px] gap-6">
        {/* Board */}
        <div>
          <GameBoard
            size={state.board_size}
            cells={state.cells}
            legalMoves={state.legal_moves}
            lastMove={state.last_move}
            humanColor={state.human_color}
            colorToPlay={state.color_to_play}
            disabled={!isHumanTurn || moveMut.isPending}
            onPlay={(m) => moveMut.mutate(m)}
          />

          {/* Bottom controls */}
          <div className="mt-5 flex items-center justify-between gap-3">
            <div className="text-xs text-ink-300">
              You play{' '}
              <span className={state.human_color === 'black' ? 'text-wood-100' : 'text-wood-100'}>
                {state.human_color === 'black' ? '● Black' : '○ White'}
              </span>{' '}
              vs{' '}
              <span className="text-wood-200">{state.agent_name}</span>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={!isHumanTurn || moveMut.isPending}
                onClick={() => moveMut.mutate('PASS')}
                className="px-4 py-2 rounded-lg border border-ink-600 text-ink-200 text-sm hover:border-ink-500 hover:text-wood-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Pass
              </button>
              <button
                type="button"
                disabled={isOver || resignMut.isPending}
                onClick={() => resignMut.mutate()}
                className="px-4 py-2 rounded-lg border border-red-700/50 text-red-300/90 text-sm hover:border-red-600 hover:text-red-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Resign
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <aside className="space-y-4">
          <TurnPanel state={state} thinking={isAgentThinking} />
          <CapturesPanel state={state} />
          <MoveListPanel state={state} />
        </aside>
      </div>

      {isOver && (
        <GameOverModal
          state={state}
          onPlayAgain={() => navigate('/setup')}
          onClose={() => navigate('/setup')}
        />
      )}
    </div>
  )
}

function TurnPanel({ state, thinking }: { state: GameState; thinking: boolean }) {
  const yourTurn = state.color_to_play === state.human_color && state.status === 'in_progress'
  return (
    <div className="rounded-2xl border border-ink-700/70 bg-ink-800/50 p-5">
      <div className="text-xs uppercase tracking-[0.2em] text-ink-300 mb-2">Turn</div>
      {state.status !== 'in_progress' ? (
        <div className="text-wood-100 font-display text-xl">Game over</div>
      ) : (
        <div className="flex items-center gap-3">
          <span
            className={
              'w-7 h-7 rounded-full ' +
              (state.color_to_play === 'black'
                ? 'bg-gradient-to-br from-ink-500 to-black shadow-stone'
                : 'bg-gradient-to-br from-white to-ink-300 shadow-stoneLight')
            }
          />
          <div className="text-wood-100 font-medium">
            {yourTurn ? 'Your move' : `${capitalize(state.color_to_play)} (AI) thinking…`}
          </div>
        </div>
      )}
      {thinking && (
        <div className="mt-3 flex items-center gap-2 text-xs text-ink-300 animate-pulse-soft">
          <span className="w-1.5 h-1.5 rounded-full bg-wood-300" />
          <span className="w-1.5 h-1.5 rounded-full bg-wood-300" />
          <span className="w-1.5 h-1.5 rounded-full bg-wood-300" />
          <span className="ml-1">searching…</span>
        </div>
      )}
    </div>
  )
}

function CapturesPanel({ state }: { state: GameState }) {
  return (
    <div className="rounded-2xl border border-ink-700/70 bg-ink-800/50 p-5">
      <div className="text-xs uppercase tracking-[0.2em] text-ink-300 mb-3">Captures</div>
      <div className="grid grid-cols-2 gap-4 text-center">
        <div>
          <div className="text-3xl font-display text-wood-100">{state.captures.black}</div>
          <div className="text-xs text-ink-300 mt-1">by Black</div>
        </div>
        <div>
          <div className="text-3xl font-display text-wood-100">{state.captures.white}</div>
          <div className="text-xs text-ink-300 mt-1">by White</div>
        </div>
      </div>
    </div>
  )
}

function MoveListPanel({ state }: { state: GameState }) {
  const ref = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [state.moves.length])
  return (
    <div className="rounded-2xl border border-ink-700/70 bg-ink-800/50 p-5">
      <div className="text-xs uppercase tracking-[0.2em] text-ink-300 mb-3">Moves</div>
      <div ref={ref} className="max-h-72 overflow-y-auto space-y-1 pr-1">
        {state.moves.length === 0 && (
          <div className="text-ink-300 text-sm italic">No moves yet.</div>
        )}
        {state.moves.map((m, i) => (
          <div
            key={i}
            className="flex items-center justify-between text-sm py-1 border-b border-ink-700/40 last:border-0"
          >
            <span className="text-ink-300 w-6">{i + 1}.</span>
            <span className="flex items-center gap-2">
              <span
                className={
                  'w-3 h-3 rounded-full ' +
                  (m.color === 'black'
                    ? 'bg-gradient-to-br from-ink-500 to-black'
                    : 'bg-gradient-to-br from-white to-ink-300')
                }
              />
              <span className="text-wood-100">{m.move}</span>
            </span>
            <span className="text-ink-300 text-xs">
              {m.by === 'human' ? 'you' : 'ai'} {m.elapsed_ms}ms
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function GameOverModal({
  state,
  onPlayAgain,
}: {
  state: GameState
  onPlayAgain: () => void
  onClose: () => void
}) {
  const ref = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    if (!ref.current) return
    const ctx = gsap.context(() => {
      gsap.from('.modal-card', {
        autoAlpha: 0,
        y: 20,
        scale: 0.95,
        duration: 0.45,
        ease: 'power3.out',
      })
      gsap.from('.modal-backdrop', { autoAlpha: 0, duration: 0.35 })
    }, ref)
    return () => ctx.revert()
  }, [])

  const winner = state.score?.winner ?? 'empty'
  const youWon = winner === state.human_color
  const tied = winner === 'empty'
  const headline = tied
    ? 'A draw'
    : youWon
      ? 'You win'
      : 'You lose'

  return (
    <div
      ref={ref}
      className="fixed inset-0 z-50 flex items-center justify-center px-4"
    >
      <div className="modal-backdrop absolute inset-0 bg-black/65 backdrop-blur-sm" />
      <div className="modal-card relative max-w-md w-full rounded-2xl border border-ink-700/70 bg-ink-800/90 p-7 shadow-board">
        <div className="text-xs uppercase tracking-[0.2em] text-ink-300 mb-2">
          {state.status === 'resigned' ? 'Resignation' : 'Result'}
        </div>
        <h2 className="font-display text-3xl text-wood-100">{headline}</h2>
        {state.score && (
          <p className="mt-3 text-ink-300 text-sm">
            Black <span className="text-wood-100">{state.score.black.toFixed(1)}</span> · White{' '}
            <span className="text-wood-100">{state.score.white.toFixed(1)}</span>
            {state.score.winner !== 'empty' && (
              <>
                {' '}
                · winner: <span className="text-wood-200 capitalize">{state.score.winner}</span>
              </>
            )}
          </p>
        )}
        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={onPlayAgain}
            className="flex-1 py-2.5 rounded-full bg-wood-300 text-ink-900 font-medium hover:bg-wood-200 transition-colors"
          >
            Play again
          </button>
          <Link
            to="/"
            className="flex-1 text-center py-2.5 rounded-full border border-ink-600 text-ink-200 hover:border-ink-500 hover:text-wood-100 transition-colors"
          >
            Home
          </Link>
        </div>
      </div>
    </div>
  )
}

function capitalize(c: ColorName): string {
  return c.charAt(0).toUpperCase() + c.slice(1)
}
