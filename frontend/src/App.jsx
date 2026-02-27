import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Order from './pages/Order'
import TrackOrder from './pages/TrackOrder'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/order" element={<Order />} />
      <Route path="/track" element={<TrackOrder />} />
      <Route path="/track/:orderId" element={<TrackOrder />} />
    </Routes>
  )
}
