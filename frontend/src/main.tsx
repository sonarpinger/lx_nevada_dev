import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

// components are held in components folder in src folder
import IndexPage from './components/IndexPage'
import About from './components/About'
import Contact from './components/Contact'

import './output.css' // output of tailwind css render

const domNode = document.getElementById('root');
if (!domNode) {
  throw new Error('No root element found');
}
const root = createRoot(domNode);
root.render(
  <BrowserRouter>
    <Routes>
      <Route index element={<IndexPage />} />
      <Route path="/" element={<IndexPage />} />
      <Route path="/about" element={<About />} />
      <Route path="/contact" element={<Contact />} />
    </Routes>
  </BrowserRouter>
);
