// Self-contained alpha-beta engine for the methodology page visualization.
// Builds a game tree of the requested shape and emits a stream of events the
// renderer plays back to show DFS order, alpha/beta updates, and pruning.

export type NodeId = string

export interface TreeNode {
  id: NodeId
  depth: number
  isMax: boolean
  children: TreeNode[]
  // Leaves only:
  leafValue?: number
}

export type ABEvent =
  | { type: 'enter'; nodeId: NodeId; alpha: number; beta: number }
  | { type: 'leaf'; nodeId: NodeId; value: number }
  | { type: 'update'; nodeId: NodeId; alpha: number; beta: number; best: number }
  | { type: 'prune'; nodeId: NodeId } // a child that was skipped due to pruning
  | { type: 'exit'; nodeId: NodeId; value: number }

export interface BuildOptions {
  depth: number
  branching: number
  seed?: number
}

// Tiny seeded PRNG so the tree is reproducible across renders for a given seed.
function mulberry32(seed: number): () => number {
  return () => {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = seed
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export function buildTree({ depth, branching, seed = 1 }: BuildOptions): TreeNode {
  const rand = mulberry32(seed)
  let counter = 0
  const next = (): NodeId => `n${counter++}`
  const make = (d: number, isMax: boolean): TreeNode => {
    if (d === 0) {
      // Leaf: integer in [-9, 9] for compact display.
      const v = Math.round((rand() * 2 - 1) * 9)
      return { id: next(), depth: d, isMax, children: [], leafValue: v }
    }
    const node: TreeNode = { id: next(), depth: d, isMax, children: [] }
    for (let i = 0; i < branching; i++) {
      node.children.push(make(d - 1, !isMax))
    }
    return node
  }
  return make(depth, true)
}

export function flatten(node: TreeNode): TreeNode[] {
  const out: TreeNode[] = []
  const walk = (n: TreeNode) => {
    out.push(n)
    n.children.forEach(walk)
  }
  walk(node)
  return out
}

export function runAlphaBeta(root: TreeNode): ABEvent[] {
  const events: ABEvent[] = []

  const recurse = (
    node: TreeNode,
    alpha: number,
    beta: number,
  ): number => {
    events.push({ type: 'enter', nodeId: node.id, alpha, beta })
    if (node.leafValue !== undefined) {
      events.push({ type: 'leaf', nodeId: node.id, value: node.leafValue })
      events.push({ type: 'exit', nodeId: node.id, value: node.leafValue })
      return node.leafValue
    }
    let best = node.isMax ? -Infinity : Infinity
    let i = 0
    for (; i < node.children.length; i++) {
      const child = node.children[i]
      const value = recurse(child, alpha, beta)
      if (node.isMax) {
        best = Math.max(best, value)
        alpha = Math.max(alpha, best)
      } else {
        best = Math.min(best, value)
        beta = Math.min(beta, best)
      }
      events.push({ type: 'update', nodeId: node.id, alpha, beta, best })
      if (alpha >= beta) {
        // Mark every remaining child (and its subtree) as pruned.
        for (let j = i + 1; j < node.children.length; j++) {
          markSubtreePruned(node.children[j], events)
        }
        break
      }
    }
    events.push({ type: 'exit', nodeId: node.id, value: best })
    return best
  }

  recurse(root, -Infinity, Infinity)
  return events
}

function markSubtreePruned(node: TreeNode, events: ABEvent[]): void {
  events.push({ type: 'prune', nodeId: node.id })
  for (const c of node.children) markSubtreePruned(c, events)
}

// Layout: assign (x, y) for each node based on a tidy in-order leaf placement.
export interface LayoutPos {
  x: number
  y: number
}

export interface Layout {
  positions: Map<NodeId, LayoutPos>
  width: number
  height: number
}

export function layoutTree(
  root: TreeNode,
  opts: { width: number; height: number; padding?: number } = { width: 800, height: 400 },
): Layout {
  const padding = opts.padding ?? 40
  const positions = new Map<NodeId, LayoutPos>()
  const leaves: TreeNode[] = []
  const collect = (n: TreeNode) => {
    if (n.children.length === 0) leaves.push(n)
    else n.children.forEach(collect)
  }
  collect(root)
  const innerWidth = opts.width - 2 * padding
  const innerHeight = opts.height - 2 * padding
  const maxDepth = root.depth // root has the highest depth value; leaves have depth 0
  leaves.forEach((leaf, i) => {
    const x = leaves.length === 1
      ? padding + innerWidth / 2
      : padding + (innerWidth * i) / (leaves.length - 1)
    const y = padding + innerHeight * ((maxDepth - leaf.depth) / Math.max(1, maxDepth))
    positions.set(leaf.id, { x, y })
  })
  // Internal nodes: x = mean of children x; y = depth-based.
  const layoutInternal = (n: TreeNode): LayoutPos => {
    if (positions.has(n.id)) return positions.get(n.id)!
    const childPositions = n.children.map(layoutInternal)
    const x = childPositions.reduce((s, p) => s + p.x, 0) / childPositions.length
    const y = padding + innerHeight * ((maxDepth - n.depth) / Math.max(1, maxDepth))
    const pos = { x, y }
    positions.set(n.id, pos)
    return pos
  }
  layoutInternal(root)
  return { positions, width: opts.width, height: opts.height }
}
