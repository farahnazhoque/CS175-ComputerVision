import { useState } from 'react'
import '../style/App.css'
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Home from './Home';
import Upload from './Upload';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/home" element={<Home />} />
      </Routes>
    </Router>
  )
}

export default App
