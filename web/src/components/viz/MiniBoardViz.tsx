import { useEffect, useMemo, useRef, useState } from 'react'
import { gsap } from 'gsap'

interface Props {
  /** Visualization mode. */
  mode: 'random' | 'greedy'
  size?: number
  loopMs?: number
}

/**
 * Small 4x4 (or sized) board that loops a stylized animation:
 *
 * - mode="random": stones pop in at random empty cells, board resets when full.
 * - mode="greedy": each empty cell gets a small score pip; the highest score
 *   is chosen and a stone drops there. The cycle restarts.
 *
 * These are educational visualizations, not real games — they exist to give
 * the viewer an at-a-glance feel for what each algorithm does.
 */
export default function MiniBoardViz({ mode, size = 4, loopMs = 850 }: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null)
  const [cells, setCells] = useState<number[]>(() => Array(size * size).fill(0))
  const [scores, setScores] = useState<number[] | null>(null)
  const [highlight, setHighlight] = useState<number | null>(null)
  const [colorToPlay, setColorToPlay] = useState<1 | 2>(1)

  const cellPx = useMemo(() => 200 / (size + 0.5), [size])
  const padding = (200 - cellPx * (size - 1)) / 2

  // Animation loop.
  useEffect(() => {
    let cancelled = false
    const tick = async () => {
      while (!cancelled) {
        await new Promise<void>((r) => setTimeout(r, loopMs))
        if (cancelled) return
        if (mode === 'random') {
          setCells((prev) => {
            const empties = prev
              .map((v, i) => (v === 0 ? i : -1))
              .filter((i) => i >= 0)
            if (empties.length === 0) {
              setColorToPlay(1)
              return Array(size * size).fill(0)
            }
            const pick = empties[Math.floor(Math.random() * empties.length)]
            const next = [...prev]
            next[pick] = colorToPlay
            return next
          })
          setColorToPlay((c) => (c === 1 ? 2 : 1))
        } else {
          // greedy: build scores, highlight max, drop a stone.
          let scoreArr: number[] | null = null
          let pick = -1
          setCells((prev) => {
            scoreArr = prev.map((v, i) => {
              if (v !== 0) return -1
              // Made-up score: prefer center + small noise.
              const r = Math.floor(i / size)
              const c = i % size
              const center = (size - 1) / 2
              const dist = Math.abs(r - center) + Math.abs(c - center)
              return Math.round(((size - dist) * 2 + Math.random() * 3) * 10) / 10
            })
            const candidates = scoreArr
              .map((s, i) => ({ s, i }))
              .filter((x) => x.s >= 0)
            if (candidates.length === 0) {
              setColorToPlay(1)
              setScores(null)
              setHighlight(null)
              return Array(size * size).fill(0)
            }
            const best = candidates.reduce((a, b) => (a.s >= b.s ? a : b))
            pick = best.i
            return prev
          })
          setScores(scoreArr)
          await new Promise<void>((r) => setTimeout(r, loopMs * 0.7))
          if (cancelled || pick < 0) continue
          setHighlight(pick)
          await new Promise<void>((r) => setTimeout(r, loopMs * 0.5))
          if (cancelled) continue
          setCells((prev) => {
            const next = [...prev]
            next[pick] = colorToPlay
            return next
          })
          setColorToPlay((c) => (c === 1 ? 2 : 1))
          setScores(null)
          setHighlight(null)
        }
      }
    }
    tick()
    return () => {
      cancelled = true
    }
  }, [mode, size, loopMs, colorToPlay])

  // Animate stones in.
  useEffect(() => {
    if (!svgRef.current) return
    const ctx = gsap.context(() => {
      gsap.from('.viz-stone', {
        scale: 0,
        autoAlpha: 0,
        duration: 0.4,
        ease: 'back.out(2.4)',
        transformOrigin: '50% 50%',
        stagger: 0.02,
      })
    }, svgRef)
    return () => ctx.revert()
  }, [cells])

  const xy = (i: number) => {
    const r = Math.floor(i / size)
    const c = i % size
    return { x: padding + c * cellPx, y: padding + r * cellPx }
  }

  return (
    <svg
      ref={svgRef}
      viewBox="0 0 200 200"
      className="w-full h-auto rounded-xl"
    >
      <defs>
        <radialGradient id="mb-board" cx="32%" cy="28%" r="85%">
          <stop offset="0%" stopColor="#dcb872" />
          <stop offset="60%" stopColor="#a87a35" />
          <stop offset="100%" stopColor="#634621" />
        </radialGradient>
        <radialGradient id="mb-black" cx="35%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#666a76" />
          <stop offset="55%" stopColor="#1d2129" />
          <stop offset="100%" stopColor="#000" />
        </radialGradient>
        <radialGradient id="mb-white" cx="35%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#fff" />
          <stop offset="65%" stopColor="#dee0e8" />
          <stop offset="100%" stopColor="#9ea2b1" />
        </radialGradient>
      </defs>

      <rect x="0" y="0" width="200" height="200" rx="12" fill="url(#mb-board)" />
      <g stroke="#3f2d16" strokeWidth="1" opacity="0.85">
        {Array.from({ length: size }).map((_, i) => (
          <g key={i}>
            <line x1={padding + i * cellPx} y1={padding} x2={padding + i * cellPx} y2={padding + (size - 1) * cellPx} />
            <line x1={padding} y1={padding + i * cellPx} x2={padding + (size - 1) * cellPx} y2={padding + i * cellPx} />
          </g>
        ))}
      </g>

      {/* Score pips (greedy mode) */}
      {scores &&
        scores.map((s, i) => {
          if (s < 0) return null
          const { x, y } = xy(i)
          const isHighlight = highlight === i
          return (
            <g key={`s-${i}`}>
              <circle
                cx={x}
                cy={y}
                r={isHighlight ? 11 : 8}
                fill={isHighlight ? '#dcb872' : '#3f2d16'}
                opacity={isHighlight ? 0.95 : 0.55}
              />
              <text
                x={x}
                y={y + 3}
                textAnchor="middle"
                fontSize="8"
                fontWeight="600"
                fill={isHighlight ? '#0d0f12' : '#dcb872'}
              >
                {s.toFixed(1)}
              </text>
            </g>
          )
        })}

      {/* Stones */}
      {cells.map((v, i) => {
        if (v === 0) return null
        const { x, y } = xy(i)
        return (
          <circle
            key={`p-${i}-${v}`}
            className="viz-stone"
            cx={x}
            cy={y}
            r={cellPx * 0.42}
            fill={v === 1 ? 'url(#mb-black)' : 'url(#mb-white)'}
          />
        )
      })}
    </svg>
  )
}
