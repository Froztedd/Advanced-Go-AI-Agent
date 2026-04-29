import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { gsap } from 'gsap'

const FEATURES = [
  {
    title: 'Five agents',
    body: 'Random, greedy, depth-2 minimax, and a tuned alpha-beta search. AlphaZero coming soon.',
  },
  {
    title: 'Real algorithms',
    body: 'Negamax, iterative deepening, phase-aware heuristics, positional superko. No tricks.',
  },
  {
    title: 'Tested engine',
    body: 'A 65-test suite pins capture, ko, suicide, and area scoring. The original CSCI 561 agent ships beside it for parity.',
  },
]

export default function LandingPage() {
  const heroRef = useRef<HTMLDivElement | null>(null)
  const orbitRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!heroRef.current || !orbitRef.current) return
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: 'power3.out' } })
      tl.from('.hero-eyebrow', { y: 12, autoAlpha: 0, duration: 0.6 })
        .from('.hero-title-line', { y: 30, autoAlpha: 0, duration: 0.9, stagger: 0.12 }, '<+0.05')
        .from('.hero-sub', { y: 18, autoAlpha: 0, duration: 0.7 }, '<+0.2')
        .from('.hero-cta', { y: 12, autoAlpha: 0, duration: 0.6, stagger: 0.08 }, '<+0.1')
        .from('.feature-card', { y: 24, autoAlpha: 0, duration: 0.7, stagger: 0.1 }, '<+0.1')

      // Orbiting stones around the hero "logo".
      gsap.to('.orbit-stone', {
        rotate: 360,
        duration: 20,
        repeat: -1,
        ease: 'none',
        transformOrigin: '120px 120px',
      })
      gsap.to('.orbit-ring', {
        rotate: -360,
        duration: 60,
        repeat: -1,
        ease: 'none',
        transformOrigin: '50% 50%',
      })

      // Subtle parallax tilt on hero.
      const onMove = (e: MouseEvent) => {
        const rect = heroRef.current!.getBoundingClientRect()
        const x = (e.clientX - rect.left) / rect.width - 0.5
        const y = (e.clientY - rect.top) / rect.height - 0.5
        gsap.to(orbitRef.current, {
          rotationY: x * 12,
          rotationX: -y * 8,
          duration: 0.8,
          ease: 'power3.out',
        })
      }
      heroRef.current!.addEventListener('mousemove', onMove)
      return () => {
        heroRef.current?.removeEventListener('mousemove', onMove)
      }
    }, heroRef)
    return () => ctx.revert()
  }, [])

  return (
    <div ref={heroRef} className="flex-1 flex flex-col">
      {/* Hero */}
      <section className="px-6 pt-16 pb-20 md:pt-24 md:pb-28">
        <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-12 items-center">
          <div>
            <p className="hero-eyebrow text-xs uppercase tracking-[0.25em] text-wood-300/80 mb-5">
              5×5 Go · 5 algorithms
            </p>
            <h1 className="font-display text-5xl md:text-7xl leading-[1.05] text-wood-50">
              <span className="hero-title-line block">Five algorithms,</span>
              <span className="hero-title-line block text-wood-300">one stone arena.</span>
            </h1>
            <p className="hero-sub mt-7 text-ink-300 max-w-lg leading-relaxed">
              Play Go on a 5×5 board against agents ranging from a uniform random baseline to a
              tuned negamax search with alpha-beta pruning, iterative deepening, and a phase-aware
              heuristic. Watch the AI's moves unfold in real time.
            </p>
            <div className="mt-9 flex items-center gap-4">
              <Link
                to="/setup"
                className="hero-cta inline-flex items-center gap-2 px-6 py-3 rounded-full bg-wood-300 text-ink-900 font-medium hover:bg-wood-200 transition-colors shadow-lg shadow-wood-500/20"
              >
                Start a game
                <span aria-hidden>→</span>
              </Link>
              <Link
                to="/methodology"
                className="hero-cta inline-flex items-center gap-2 px-6 py-3 rounded-full border border-ink-600 text-ink-200 hover:border-ink-500 hover:text-wood-100 transition-colors"
              >
                What's inside
              </Link>
            </div>
          </div>

          {/* Hero visual: a SVG-rendered Go corner with orbiting stones */}
          <div
            ref={orbitRef}
            className="relative aspect-square w-full max-w-md mx-auto"
            style={{ perspective: '1200px' }}
          >
            <svg viewBox="0 0 240 240" className="w-full h-full">
              {/* board pad */}
              <defs>
                <radialGradient id="wood-grad" cx="35%" cy="30%" r="80%">
                  <stop offset="0%" stopColor="#dcb872" />
                  <stop offset="60%" stopColor="#a87a35" />
                  <stop offset="100%" stopColor="#634621" />
                </radialGradient>
                <radialGradient id="black-stone" cx="35%" cy="30%" r="70%">
                  <stop offset="0%" stopColor="#5a5e6a" />
                  <stop offset="60%" stopColor="#15181d" />
                  <stop offset="100%" stopColor="#000" />
                </radialGradient>
                <radialGradient id="white-stone" cx="35%" cy="30%" r="70%">
                  <stop offset="0%" stopColor="#fff" />
                  <stop offset="70%" stopColor="#dadce4" />
                  <stop offset="100%" stopColor="#9ea2b1" />
                </radialGradient>
              </defs>
              <rect x="20" y="20" width="200" height="200" rx="14" fill="url(#wood-grad)" />
              {/* grid */}
              {[0, 1, 2, 3, 4].map((i) => (
                <g key={i} stroke="#3f2d16" strokeWidth="1.5" opacity="0.85">
                  <line x1={50 + i * 35} y1={50} x2={50 + i * 35} y2={190} />
                  <line x1={50} y1={50 + i * 35} x2={190} y2={50 + i * 35} />
                </g>
              ))}
              {/* center hoshi */}
              <circle cx={120} cy={120} r={3} fill="#3f2d16" />
              {/* central decorative stone */}
              <circle className="orbit-ring" cx={120} cy={120} r={62} fill="none" stroke="#3f2d16" strokeWidth="0.8" strokeDasharray="2 4" opacity="0.55" />
              <circle cx={120} cy={120} r={16} fill="url(#black-stone)" />
              {/* orbiting stones */}
              <g>
                <circle className="orbit-stone" cx={170} cy={120} r={9} fill="url(#white-stone)" />
                <circle className="orbit-stone" cx={70} cy={120} r={7} fill="url(#black-stone)" />
                <circle className="orbit-stone" cx={120} cy={70} r={6} fill="url(#white-stone)" />
                <circle className="orbit-stone" cx={120} cy={170} r={8} fill="url(#black-stone)" />
              </g>
            </svg>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-6 pb-24">
        <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="feature-card rounded-2xl border border-ink-700/70 bg-ink-800/40 p-7 hover:border-wood-500/40 transition-colors"
            >
              <h3 className="font-display text-2xl text-wood-100 mb-3">{f.title}</h3>
              <p className="text-ink-300 leading-relaxed">{f.body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
