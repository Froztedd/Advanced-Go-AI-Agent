import { useEffect, useMemo, useRef, useState } from 'react'
import { gsap } from 'gsap'
import type { ColorName } from '../lib/types'

interface Props {
  size: number
  cells: number[][]
  legalMoves: string[]
  lastMove: string | null
  humanColor: ColorName
  colorToPlay: ColorName
  disabled: boolean
  onPlay: (move: string) => void
}

const PADDING = 36
const VIEWBOX = 480
const HOSHI = (size: number): Array<[number, number]> => {
  if (size === 5) return [[2, 2]]
  return []
}

export default function GameBoard(props: Props) {
  const { size, cells, legalMoves, lastMove, humanColor, colorToPlay, disabled, onPlay } = props
  const cell = (VIEWBOX - 2 * PADDING) / (size - 1)
  const stoneR = cell * 0.46

  const ref = useRef<SVGSVGElement | null>(null)
  const [hover, setHover] = useState<[number, number] | null>(null)
  const prevCellsRef = useRef<number[][] | null>(null)

  // Animate stones on changes: new stones drop in, captured stones fade out.
  useEffect(() => {
    if (!ref.current) return
    const ctx = gsap.context(() => {
      const prev = prevCellsRef.current
      if (!prev) {
        // First render — animate every existing stone.
        gsap.from('.stone', {
          scale: 0,
          autoAlpha: 0,
          duration: 0.45,
          ease: 'back.out(2.2)',
          stagger: 0.02,
          transformOrigin: '50% 50%',
        })
      } else {
        const newStones: Element[] = []
        const removedStones: Element[] = []
        for (let r = 0; r < size; r++) {
          for (let c = 0; c < size; c++) {
            const before = prev[r][c]
            const after = cells[r][c]
            const el = ref.current!.querySelector(`[data-cell="${r}-${c}"]`)
            if (!el) continue
            if (before === 0 && after !== 0) newStones.push(el)
            if (before !== 0 && after === 0) removedStones.push(el)
          }
        }
        if (removedStones.length) {
          gsap.fromTo(
            removedStones,
            { scale: 1, autoAlpha: 1 },
            {
              scale: 1.4,
              autoAlpha: 0,
              duration: 0.32,
              ease: 'power2.out',
              transformOrigin: '50% 50%',
            },
          )
        }
        if (newStones.length) {
          gsap.from(newStones, {
            scale: 0,
            autoAlpha: 0,
            duration: 0.5,
            ease: 'back.out(2.4)',
            transformOrigin: '50% 50%',
          })
        }
      }
    }, ref)
    prevCellsRef.current = cells.map((row) => [...row])
    return () => ctx.revert()
  }, [cells, size, lastMove])

  const legalSet = useMemo(() => new Set(legalMoves), [legalMoves])

  const xy = (r: number, c: number) => ({ x: PADDING + c * cell, y: PADDING + r * cell })
  const isLegal = (r: number, c: number) => legalSet.has(`${r},${c}`)
  const isHumanTurn = humanColor === colorToPlay && !disabled

  return (
    <div className="relative w-full max-w-[640px] aspect-square mx-auto">
      <svg
        ref={ref}
        viewBox={`0 0 ${VIEWBOX} ${VIEWBOX}`}
        className="w-full h-full select-none"
        onMouseLeave={() => setHover(null)}
      >
        <defs>
          <radialGradient id="board-grad" cx="32%" cy="28%" r="85%">
            <stop offset="0%" stopColor="#dcb872" />
            <stop offset="60%" stopColor="#a87a35" />
            <stop offset="100%" stopColor="#634621" />
          </radialGradient>
          <radialGradient id="black-stone-grad" cx="35%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#666a76" />
            <stop offset="55%" stopColor="#1d2129" />
            <stop offset="100%" stopColor="#000" />
          </radialGradient>
          <radialGradient id="white-stone-grad" cx="35%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="65%" stopColor="#dee0e8" />
            <stop offset="100%" stopColor="#9da2b1" />
          </radialGradient>
          <filter id="stone-shadow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="2" stdDeviation="2.5" floodColor="#000" floodOpacity="0.55" />
          </filter>
        </defs>

        {/* Board */}
        <rect x="0" y="0" width={VIEWBOX} height={VIEWBOX} rx="20" fill="url(#board-grad)" />

        {/* Subtle wood grain via faint horizontal stripes */}
        <g opacity="0.07">
          {Array.from({ length: 24 }).map((_, i) => (
            <line
              key={i}
              x1="0"
              y1={(i + 0.5) * (VIEWBOX / 24)}
              x2={VIEWBOX}
              y2={(i + 0.5) * (VIEWBOX / 24)}
              stroke="#3f2d16"
              strokeWidth="1"
            />
          ))}
        </g>

        {/* Grid */}
        <g stroke="#3f2d16" strokeWidth="1.5" opacity="0.85" strokeLinecap="round">
          {Array.from({ length: size }).map((_, i) => (
            <g key={i}>
              <line
                x1={PADDING + i * cell}
                y1={PADDING}
                x2={PADDING + i * cell}
                y2={VIEWBOX - PADDING}
              />
              <line
                x1={PADDING}
                y1={PADDING + i * cell}
                x2={VIEWBOX - PADDING}
                y2={PADDING + i * cell}
              />
            </g>
          ))}
        </g>

        {/* Hoshi points */}
        {HOSHI(size).map(([r, c]) => {
          const { x, y } = xy(r, c)
          return <circle key={`${r}-${c}`} cx={x} cy={y} r={3.5} fill="#3f2d16" />
        })}

        {/* Click / hover overlay (only on empty + legal cells when human's turn) */}
        {Array.from({ length: size }).map((_, r) =>
          Array.from({ length: size }).map((__, c) => {
            const empty = cells[r][c] === 0
            const playable = isHumanTurn && empty && isLegal(r, c)
            const { x, y } = xy(r, c)
            return (
              <rect
                key={`hit-${r}-${c}`}
                x={x - cell / 2}
                y={y - cell / 2}
                width={cell}
                height={cell}
                fill="transparent"
                style={{ cursor: playable ? 'pointer' : 'default' }}
                onMouseEnter={() => playable && setHover([r, c])}
                onClick={() => playable && onPlay(`${r},${c}`)}
              />
            )
          }),
        )}

        {/* Hover preview */}
        {hover && cells[hover[0]][hover[1]] === 0 && isHumanTurn && (
          <circle
            cx={xy(hover[0], hover[1]).x}
            cy={xy(hover[0], hover[1]).y}
            r={stoneR}
            fill={
              humanColor === 'black' ? 'url(#black-stone-grad)' : 'url(#white-stone-grad)'
            }
            opacity="0.5"
            pointerEvents="none"
          />
        )}

        {/* Stones */}
        {cells.flatMap((row, r) =>
          row.map((v, c) => {
            if (v === 0) return null
            const { x, y } = xy(r, c)
            return (
              <circle
                key={`s-${r}-${c}`}
                data-cell={`${r}-${c}`}
                className="stone"
                cx={x}
                cy={y}
                r={stoneR}
                fill={v === 1 ? 'url(#black-stone-grad)' : 'url(#white-stone-grad)'}
                filter="url(#stone-shadow)"
              />
            )
          }),
        )}
      </svg>
    </div>
  )
}
