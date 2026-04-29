import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { gsap } from 'gsap'
import AlphaBetaViz from '../components/viz/AlphaBetaViz'
import MiniBoardViz from '../components/viz/MiniBoardViz'

type Difficulty = 'easy' | 'medium' | 'hard'

const DIFFICULTY_PRESETS: Record<Difficulty, { depth: number; branching: number; stepMs: number }> = {
  easy:   { depth: 2, branching: 2, stepMs: 700 },
  medium: { depth: 3, branching: 3, stepMs: 520 },
  hard:   { depth: 4, branching: 3, stepMs: 380 },
}

export default function MethodologyPage() {
  const [difficulty, setDifficulty] = useState<Difficulty>('medium')
  const [showPruning, setShowPruning] = useState(true)
  const [seed, setSeed] = useState(7)
  const heroRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!heroRef.current) return
    const ctx = gsap.context(() => {
      gsap.from('.method-eyebrow', { y: 12, autoAlpha: 0, duration: 0.5 })
      gsap.from('.method-title', { y: 22, autoAlpha: 0, duration: 0.7, ease: 'power3.out', delay: 0.05 })
      gsap.from('.method-sub', { y: 14, autoAlpha: 0, duration: 0.6, delay: 0.18 })
      gsap.from('.method-card', { y: 24, autoAlpha: 0, duration: 0.6, ease: 'power3.out', stagger: 0.1, delay: 0.25 })
    }, heroRef)
    return () => ctx.revert()
  }, [])

  const preset = DIFFICULTY_PRESETS[difficulty]

  return (
    <div ref={heroRef} className="px-6 py-14 md:py-20 max-w-6xl mx-auto w-full">
      {/* Hero */}
      <div className="max-w-3xl">
        <p className="method-eyebrow text-xs uppercase tracking-[0.25em] text-wood-300/80 mb-4">
          What's inside
        </p>
        <h1 className="method-title font-display text-4xl md:text-6xl text-wood-50 leading-[1.05]">
          How the agents think.
        </h1>
        <p className="method-sub mt-5 text-ink-300 leading-relaxed max-w-2xl">
          Five algorithms, ranked from "any legal move" to a tuned negamax search with
          alpha-beta pruning and iterative deepening. Watch each one in action below — and play
          with the difficulty knob on the alpha-beta tree to see how pruning saves work.
        </p>
        <div className="mt-7">
          <Link
            to="/setup"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-wood-300 text-ink-900 font-medium hover:bg-wood-200 transition-colors"
          >
            Skip to play
            <span aria-hidden>→</span>
          </Link>
        </div>
      </div>

      <div className="mt-14 space-y-6">
        {/* Random */}
        <AgentSection
          eyebrow="Strength 1"
          title="Random"
          subtitle="The baseline"
          body="Picks any legal placement uniformly at random. No board understanding, no goals. Useful as a calibration point: every other agent should beat it consistently."
          viz={<MiniBoardViz mode="random" />}
        />

        {/* Greedy */}
        <AgentSection
          eyebrow="Strength 2"
          title="Greedy"
          subtitle="One ply, no search"
          body="Scores every legal move with a small heuristic — capture value, post-move liberties, distance to center, friendly neighbors — then picks the highest. Fast and surprisingly hard to beat early in a game, but blind to anything more than one move away."
          viz={<MiniBoardViz mode="greedy" />}
        />

        {/* Minimax */}
        <AgentSection
          eyebrow="Strength 3"
          title="Minimax"
          subtitle="Depth-2 lookahead, no pruning"
          body="Builds the full game tree two ply deep, evaluates every leaf with a material + liberty heuristic, then propagates the values up: maximizing for itself at each MAX node, minimizing for the opponent at each MIN node. The strict midpoint between greedy and alpha-beta — same eval, but exhaustively expanded."
          viz={
            <AlphaBetaViz
              key={`mm-${preset.depth}-${preset.branching}-${seed}`}
              depth={preset.depth - 1 || 2}
              branching={Math.min(preset.branching, 2)}
              showPruning={false}
              stepMs={preset.stepMs}
              seed={seed}
            />
          }
          wide
        />

        {/* Alpha-Beta — the showpiece */}
        <div className="method-card rounded-2xl border border-ink-700/70 bg-ink-800/50 overflow-hidden">
          <div className="px-7 pt-7">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-wood-300/80">
                  Strength 4–5
                </p>
                <h2 className="font-display text-3xl text-wood-100 mt-1">Alpha-Beta</h2>
                <p className="text-sm text-ink-300">
                  Negamax search with alpha-beta pruning + iterative deepening
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <label className="text-xs uppercase tracking-[0.2em] text-ink-300 mr-2">
                  Difficulty
                </label>
                {(['easy', 'medium', 'hard'] as Difficulty[]).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDifficulty(d)}
                    className={
                      'px-3 py-1.5 rounded-full text-xs uppercase tracking-wider transition-colors ' +
                      (difficulty === d
                        ? 'bg-wood-300 text-ink-900'
                        : 'border border-ink-600 text-ink-200 hover:border-ink-500')
                    }
                  >
                    {d}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => setShowPruning((v) => !v)}
                  className={
                    'ml-2 px-3 py-1.5 rounded-full text-xs uppercase tracking-wider transition-colors border ' +
                    (showPruning
                      ? 'border-wood-400 bg-wood-500/10 text-wood-100'
                      : 'border-ink-600 text-ink-200 hover:border-ink-500')
                  }
                  title="Toggle alpha-beta cutoff"
                >
                  {showPruning ? 'pruning on' : 'pruning off'}
                </button>
                <button
                  type="button"
                  onClick={() => setSeed((s) => s + 1)}
                  className="px-3 py-1.5 rounded-full text-xs uppercase tracking-wider border border-ink-600 text-ink-200 hover:border-ink-500 transition-colors"
                  title="Generate a fresh tree"
                >
                  shuffle
                </button>
              </div>
            </div>

            <p className="text-ink-300 leading-relaxed mt-5 max-w-3xl">
              At each MAX node the agent tracks the best value it has seen so far (α). At each
              MIN node it tracks the worst (β). The moment a child's value reaches a point where
              the opponent would never let the search reach this branch (α ≥ β), the rest of the
              children are skipped — that's the dashed branches below. The bigger the tree, the
              more pruning saves you.
            </p>
          </div>

          <div className="px-4 md:px-6 pb-6 pt-4 mt-2 bg-ink-900/40 border-t border-ink-700/60">
            <AlphaBetaViz
              key={`ab-${preset.depth}-${preset.branching}-${showPruning}-${seed}`}
              depth={preset.depth}
              branching={preset.branching}
              showPruning={showPruning}
              stepMs={preset.stepMs}
              seed={seed}
            />
          </div>
        </div>

        {/* Footer note */}
        <div className="method-card text-center text-ink-300 text-sm pt-6">
          Convinced?{' '}
          <Link to="/setup" className="text-wood-200 hover:text-wood-100 underline-offset-4 hover:underline">
            Start a game →
          </Link>
        </div>
      </div>
    </div>
  )
}

function AgentSection(props: {
  eyebrow: string
  title: string
  subtitle: string
  body: string
  viz: React.ReactNode
  wide?: boolean
}) {
  return (
    <section className="method-card rounded-2xl border border-ink-700/70 bg-ink-800/50 overflow-hidden">
      <div
        className={
          'grid gap-6 ' +
          (props.wide ? 'lg:grid-cols-[1fr_1.4fr]' : 'lg:grid-cols-[1fr_220px]') +
          ' items-center p-7'
        }
      >
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-wood-300/80">{props.eyebrow}</p>
          <h2 className="font-display text-3xl text-wood-100 mt-1">{props.title}</h2>
          <p className="text-sm text-ink-300">{props.subtitle}</p>
          <p className="text-ink-300 mt-4 leading-relaxed">{props.body}</p>
        </div>
        <div className="w-full">{props.viz}</div>
      </div>
    </section>
  )
}
