import { useState } from 'react'
import './App.css'
import Register from './pages/Register'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

function App() {
  const [count, setCount] = useState(0)

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth/register" element={<Register />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
