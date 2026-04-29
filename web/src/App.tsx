import { Route, Routes } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import SetupPage from './pages/SetupPage'
import GamePage from './pages/GamePage'
import MethodologyPage from './pages/MethodologyPage'
import Header from './components/Header'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 flex flex-col">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/setup" element={<SetupPage />} />
          <Route path="/game/:gameId" element={<GamePage />} />
          <Route path="/methodology" element={<MethodologyPage />} />
        </Routes>
      </main>
    </div>
  )
}
