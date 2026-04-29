import { useEffect, useMemo, useRef, useState } from 'react'
import { gsap } from 'gsap'
import {
  buildTree,
  flatten,
  layoutTree,
  runAlphaBeta,
  type ABEvent,
  type NodeId,
  type TreeNode,
} from '../../lib/alphabeta'

interface Props {
  depth: number
  branching: number
  showPruning: boolean
  /** Step delay in ms. */
  stepMs?: number
  seed?: number
}

interface NodeRuntime {
  alpha: number
  beta: number
  best?: number
  visited: boolean
  active: boolean
  pruned: boolean
  leafReturned?: number
}

const DEFAULT_RUNTIME: NodeRuntime = {
  alpha: -Infinity,
  beta: Infinity,
  visited: false,
  active: false,
  pruned: false,
}

const VIEWBOX_W = 880
const VIEWBOX_H = 380

export default function AlphaBetaViz({
  depth,
  branching,
  showPruning,
  stepMs = 520,
  seed = 7,
}: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null)

  const tree = useMemo<TreeNode>(
    () => buildTree({ depth, branching, seed }),
    [depth, branching, seed],
  )
  const flatNodes = useMemo(() => flatten(tree), [tree])
  const layout = useMemo(
    () => layoutTree(tree, { width: VIEWBOX_W, height: VIEWBOX_H }),
    [tree],
  )
  const events = useMemo(() => runAlphaBeta(tree), [tree])

  const [runtime, setRuntime] = useState<Map<NodeId, NodeRuntime>>(() =>
    initialRuntime(flatNodes),
  )
  const [eventIdx, setEventIdx] = useState(0)
  const [stats, setStats] = useState({ visited: 0, pruned: 0 })

  // Reset runtime whenever the underlying tree (depth/branching/seed) changes.
  useEffect(() => {
    setRuntime(initialRuntime(flatNodes))
    setEventIdx(0)
    setStats({ visited: 0, pruned: 0 })
  }, [flatNodes])

  // Animation timer: emit one event per `stepMs`. After the last event, wait
  // a beat and start over.
  useEffect(() => {
    if (events.length === 0) return
    const handle = window.setTimeout(
      () => {
        if (eventIdx >= events.length) {
          // Pause then restart the loop.
          setRuntime(initialRuntime(flatNodes))
          setEventIdx(0)
          setStats({ visited: 0, pruned: 0 })
          return
        }
        const evt = events[eventIdx]
        applyEvent(evt, showPruning, setRuntime, setStats)
        setEventIdx((i) => i + 1)
      },
      eventIdx === events.length ? stepMs * 3 : stepMs,
    )
    return () => window.clearTimeout(handle)
  }, [eventIdx, events, flatNodes, stepMs, showPruning])

  // GSAP pulse on the active node whenever runtime changes.
  useEffect(() => {
    if (!svgRef.current) return
    const active = svgRef.current.querySelector('.node-active')
    if (active) {
      gsap.fromTo(
        active,
        { scale: 0.8 },
        {
          scale: 1.15,
          duration: 0.35,
          yoyo: true,
          repeat: 1,
          ease: 'power2.out',
          transformOrigin: '50% 50%',
        },
      )
    }
  }, [runtime])

  return (
    <div className="w-full">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${VIEWBOX_W} ${VIEWBOX_H}`}
        className="w-full h-auto"
      >
        <defs>
          <radialGradient id="ab-max" cx="35%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#ead4a4" />
            <stop offset="80%" stopColor="#a87a35" />
            <stop offset="100%" stopColor="#634621" />
          </radialGradient>
          <radialGradient id="ab-min" cx="35%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#5b6373" />
            <stop offset="80%" stopColor="#2a2f39" />
            <stop offset="100%" stopColor="#0d0f12" />
          </radialGradient>
          <radialGradient id="ab-leaf" cx="35%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#f5ead2" />
            <stop offset="100%" stopColor="#c69b4d" />
          </radialGradient>
        </defs>

        {/* Edges */}
        {flatNodes.map((n) =>
          n.children.map((c) => {
            const a = layout.positions.get(n.id)
            const b = layout.positions.get(c.id)
            if (!a || !b) return null
            const childRt = runtime.get(c.id) ?? DEFAULT_RUNTIME
            return (
              <line
                key={`e-${n.id}-${c.id}`}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                stroke={childRt.pruned ? '#5b6373' : '#85602a'}
                strokeWidth={childRt.visited ? 1.8 : 1.1}
                strokeDasharray={childRt.pruned ? '4 4' : undefined}
                opacity={childRt.pruned ? 0.35 : 0.85}
              />
            )
          }),
        )}

        {/* Nodes */}
        {flatNodes.map((n) => {
          const pos = layout.positions.get(n.id)
          if (!pos) return null
          const rt = runtime.get(n.id) ?? DEFAULT_RUNTIME
          const isLeaf = n.children.length === 0
          const fill = isLeaf
            ? 'url(#ab-leaf)'
            : n.isMax
              ? 'url(#ab-max)'
              : 'url(#ab-min)'
          const r = isLeaf ? 14 : 18
          return (
            <g
              key={n.id}
              opacity={rt.pruned ? 0.35 : 1}
              className={rt.active ? 'node-active' : undefined}
              style={{ transition: 'opacity 0.3s ease' }}
            >
              <circle
                cx={pos.x}
                cy={pos.y}
                r={r}
                fill={fill}
                stroke={
                  rt.active
                    ? '#dcb872'
                    : rt.visited
                      ? '#a87a35'
                      : '#3f2d16'
                }
                strokeWidth={rt.active ? 3 : rt.visited ? 1.8 : 1}
              />
              {/* Leaf value */}
              {isLeaf && (
                <text
                  x={pos.x}
                  y={pos.y + 4}
                  textAnchor="middle"
                  fontSize="13"
                  fontWeight="600"
                  fill="#3f2d16"
                  pointerEvents="none"
                >
                  {n.leafValue}
                </text>
              )}
              {/* α / β labels for internal nodes after they have been visited */}
              {!isLeaf && rt.visited && (
                <text
                  x={pos.x}
                  y={pos.y - 24}
                  textAnchor="middle"
                  fontSize="10"
                  fill={n.isMax ? '#ead4a4' : '#dee0e8'}
                  pointerEvents="none"
                >
                  α={fmt(rt.alpha)} β={fmt(rt.beta)}
                </text>
              )}
              {/* "Best so far" inside internal node */}
              {!isLeaf && rt.best !== undefined && (
                <text
                  x={pos.x}
                  y={pos.y + 4}
                  textAnchor="middle"
                  fontSize="12"
                  fontWeight="700"
                  fill={n.isMax ? '#3f2d16' : '#f5ead2'}
                  pointerEvents="none"
                >
                  {fmt(rt.best)}
                </text>
              )}
              {/* MAX/MIN tag for unfinished internal nodes */}
              {!isLeaf && rt.best === undefined && (
                <text
                  x={pos.x}
                  y={pos.y + 4}
                  textAnchor="middle"
                  fontSize="9"
                  fontWeight="600"
                  fill={n.isMax ? '#3f2d16' : '#f5ead2'}
                  pointerEvents="none"
                >
                  {n.isMax ? 'MAX' : 'MIN'}
                </text>
              )}
            </g>
          )
        })}
      </svg>

      {/* Legend + stats */}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-ink-300">
        <div className="flex items-center gap-4">
          <LegendDot fill="url(#ab-max)" label="MAX node (us)" />
          <LegendDot fill="url(#ab-min)" label="MIN node (opponent)" />
          <LegendDot fill="url(#ab-leaf)" label="Leaf eval" />
          {showPruning && (
            <span className="opacity-80">Dashed branches = pruned by α≥β cutoff</span>
          )}
        </div>
        <div className="font-mono text-ink-300">
          visited <span className="text-wood-100">{stats.visited}</span>
          {showPruning && (
            <>
              {' · '}pruned <span className="text-wood-100">{stats.pruned}</span>
            </>
          )}
          {' / '}
          <span className="text-wood-200">{flatNodes.length}</span>
        </div>
      </div>
    </div>
  )
}

function initialRuntime(nodes: TreeNode[]): Map<NodeId, NodeRuntime> {
  const m = new Map<NodeId, NodeRuntime>()
  for (const n of nodes) {
    m.set(n.id, {
      alpha: -Infinity,
      beta: Infinity,
      visited: false,
      active: false,
      pruned: false,
    })
  }
  return m
}

function applyEvent(
  evt: ABEvent,
  showPruning: boolean,
  setRuntime: React.Dispatch<React.SetStateAction<Map<NodeId, NodeRuntime>>>,
  setStats: React.Dispatch<React.SetStateAction<{ visited: number; pruned: number }>>,
) {
  setRuntime((prev) => {
    const next = new Map(prev)
    // Clear `active` from everyone first; we'll set the new active below.
    for (const [k, v] of next) {
      if (v.active) next.set(k, { ...v, active: false })
    }
    const cur = next.get(evt.nodeId)!
    switch (evt.type) {
      case 'enter':
        next.set(evt.nodeId, {
          ...cur,
          active: true,
          visited: true,
          alpha: evt.alpha,
          beta: evt.beta,
        })
        break
      case 'leaf':
        next.set(evt.nodeId, { ...cur, leafReturned: evt.value, best: evt.value })
        break
      case 'update':
        next.set(evt.nodeId, {
          ...cur,
          alpha: evt.alpha,
          beta: evt.beta,
          best: evt.best,
        })
        break
      case 'prune':
        if (showPruning) {
          next.set(evt.nodeId, { ...cur, pruned: true })
        } else {
          // When pruning is disabled (minimax mode), still visit them.
          next.set(evt.nodeId, { ...cur, visited: true })
        }
        break
      case 'exit':
        next.set(evt.nodeId, { ...cur, active: false, best: evt.value })
        break
    }
    return next
  })
  setStats((s) => {
    if (evt.type === 'enter') return { ...s, visited: s.visited + 1 }
    if (evt.type === 'prune' && showPruning) return { ...s, pruned: s.pruned + 1 }
    return s
  })
}

function fmt(v: number): string {
  if (v === Infinity) return '+∞'
  if (v === -Infinity) return '−∞'
  return String(v)
}

function LegendDot({ fill, label }: { fill: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <svg width="14" height="14">
        <circle cx="7" cy="7" r="6" fill={fill} stroke="#3f2d16" strokeWidth="1" />
      </svg>
      <span>{label}</span>
    </span>
  )
}
