import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { gsap } from 'gsap'
import { api } from '../lib/api'
import type { ColorName } from '../lib/types'

const TIME_PRESETS: { label: string; value: number }[] = [
  { label: 'Fast (1s)', value: 1 },
  { label: 'Normal (2s)', value: 2 },
  { label: 'Patient (5s)', value: 5 },
]

export default function SetupPage() {
  const navigate = useNavigate()
  const containerRef = useRef<HTMLDivElement | null>(null)
  const agentsQ = useQuery({ queryKey: ['agents'], queryFn: api.listAgents })
  const [color, setColor] = useState<ColorName>('black')
  const [agentName, setAgentName] = useState<string | null>(null)
  const [timeLimit, setTimeLimit] = useState(2)

  useEffect(() => {
    if (agentsQ.data && agentName === null) {
      setAgentName('greedy')
    }
  }, [agentsQ.data, agentName])

  useEffect(() => {
    if (!containerRef.current) return
    const ctx = gsap.context(() => {
      gsap.from('.setup-card', {
        autoAlpha: 0,
        y: 24,
        duration: 0.6,
        ease: 'power3.out',
      })
      gsap.from('.setup-section', {
        autoAlpha: 0,
        y: 16,
        duration: 0.5,
        ease: 'power2.out',
        stagger: 0.08,
        delay: 0.15,
      })
    }, containerRef)
    return () => ctx.revert()
  }, [])

  const startMut = useMutation({
    mutationFn: () =>
      api.createGame({
        human_color: color,
        agent: agentName ?? 'greedy',
        time_limit: timeLimit,
        board_size: 5,
      }),
    onSuccess: (state) => {
      navigate(`/game/${state.game_id}`)
    },
  })

  return (
    <div ref={containerRef} className="px-6 py-16 flex-1 flex items-start justify-center">
      <div className="setup-card max-w-2xl w-full rounded-2xl border border-ink-700/70 bg-ink-800/50 p-8 shadow-board">
        <h1 className="font-display text-3xl text-wood-100 mb-2">New game</h1>
        <p className="text-ink-300 mb-8 text-sm">
          Pick your color, an opponent, and a per-move budget. Larger budgets give the AI more
          search depth.
        </p>

        {/* Color selection */}
        <section className="setup-section mb-7">
          <h2 className="text-xs uppercase tracking-[0.2em] text-ink-300 mb-3">Your color</h2>
          <div className="grid grid-cols-2 gap-3">
            <ColorButton
              active={color === 'black'}
              onClick={() => setColor('black')}
              label="Black"
              hint="Plays first"
              dark
            />
            <ColorButton
              active={color === 'white'}
              onClick={() => setColor('white')}
              label="White"
              hint="Receives 2.5 komi"
              dark={false}
            />
          </div>
        </section>

        {/* Agent selection */}
        <section className="setup-section mb-7">
          <h2 className="text-xs uppercase tracking-[0.2em] text-ink-300 mb-3">Opponent</h2>
          {agentsQ.isLoading && <p className="text-ink-300 text-sm">Loading agents…</p>}
          {agentsQ.isError && (
            <p className="text-red-400 text-sm">
              Could not reach the API at <code>localhost:8000</code>. Is the backend running?
            </p>
          )}
          {agentsQ.data && (
            <div className="grid gap-2">
              {agentsQ.data.map((a) => (
                <button
                  key={a.name}
                  type="button"
                  onClick={() => setAgentName(a.name)}
                  className={
                    'text-left rounded-xl border px-4 py-3 transition-colors ' +
                    (agentName === a.name
                      ? 'border-wood-400 bg-wood-500/10'
                      : 'border-ink-700 hover:border-ink-500 bg-ink-900/40')
                  }
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-wood-100">{a.label}</span>
                    <StrengthDots strength={a.strength} />
                  </div>
                  <p className="mt-1 text-sm text-ink-300">{a.description}</p>
                </button>
              ))}
            </div>
          )}
        </section>

        {/* Time limit */}
        <section className="setup-section mb-8">
          <h2 className="text-xs uppercase tracking-[0.2em] text-ink-300 mb-3">Per-move budget</h2>
          <div className="flex gap-2">
            {TIME_PRESETS.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => setTimeLimit(t.value)}
                className={
                  'flex-1 px-4 py-2.5 rounded-lg border text-sm transition-colors ' +
                  (timeLimit === t.value
                    ? 'border-wood-400 bg-wood-500/10 text-wood-100'
                    : 'border-ink-700 text-ink-200 hover:border-ink-500')
                }
              >
                {t.label}
              </button>
            ))}
          </div>
        </section>

        {startMut.isError && (
          <p className="text-red-400 text-sm mb-3">
            {(startMut.error as Error).message}
          </p>
        )}
        <button
          type="button"
          disabled={!agentName || startMut.isPending}
          onClick={() => startMut.mutate()}
          className="w-full py-3 rounded-full bg-wood-300 text-ink-900 font-medium hover:bg-wood-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-wood-500/20"
        >
          {startMut.isPending ? 'Starting…' : 'Begin'}
        </button>
      </div>
    </div>
  )
}

function ColorButton(props: {
  active: boolean
  onClick: () => void
  label: string
  hint: string
  dark: boolean
}) {
  return (
    <button
      type="button"
      onClick={props.onClick}
      className={
        'flex items-center gap-3 px-4 py-4 rounded-xl border transition-colors ' +
        (props.active
          ? 'border-wood-400 bg-wood-500/10'
          : 'border-ink-700 hover:border-ink-500 bg-ink-900/40')
      }
    >
      <span
        className={
          'w-9 h-9 rounded-full ' +
          (props.dark
            ? 'bg-gradient-to-br from-ink-500 to-black shadow-stone'
            : 'bg-gradient-to-br from-white to-ink-300 shadow-stoneLight')
        }
      />
      <span className="text-left">
        <span className="block text-wood-100 font-medium">{props.label}</span>
        <span className="block text-xs text-ink-300">{props.hint}</span>
      </span>
    </button>
  )
}

function StrengthDots({ strength }: { strength: number }) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={
            'w-1.5 h-1.5 rounded-full ' +
            (i <= strength ? 'bg-wood-300' : 'bg-ink-600')
          }
        />
      ))}
    </div>
  )
}
