import { useState, useEffect } from 'react'
import api from '../lib/api'

export default function Printers() {
  const [printers, setPrinters] = useState([])
  const [claimCode, setClaimCode] = useState('')
  const [claimName, setClaimName] = useState('')
  const [claiming, setClaiming] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => { loadPrinters() }, [])

  async function loadPrinters() {
    try {
      const { data } = await api.get('/orders/printers/')
      setPrinters(data)
    } catch {
      setPrinters([])
    }
  }

  async function handleClaim(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setClaiming(true)
    try {
      await api.post('/orders/printers/claim', {
        claim_code: claimCode.toUpperCase().trim(),
        name: claimName.trim() || 'Kitchen Printer',
      })
      setSuccess('Printer claimed successfully.')
      setClaimCode('')
      setClaimName('')
      loadPrinters()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to claim printer.')
    } finally {
      setClaiming(false)
    }
  }

  async function handleUnclaim(id) {
    if (!confirm('Remove this printer from your kitchen?')) return
    try {
      await api.delete(`/orders/printers/${id}`)
      loadPrinters()
    } catch {
      setError('Failed to remove printer.')
    }
  }

  function formatLastSeen(ts) {
    if (!ts) return 'Never'
    const d = new Date(ts)
    const diff = (Date.now() - d) / 1000
    if (diff < 60) return 'Just now'
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return d.toLocaleDateString()
  }

  return (
    <div className="max-w-2xl space-y-8">
      <h1 className="text-2xl font-bold text-brand-text">Printers</h1>

      {success && <p className="text-green-600 text-sm">{success}</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {/* Claimed printers */}
      <div className="bg-brand-surface rounded-xl shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-800">Your Printers</h2>
        {printers.length === 0 ? (
          <p className="text-gray-400 text-sm">No printers claimed yet. Power on your ByteOrder printer and enter the claim code below.</p>
        ) : (
          <div className="space-y-3">
            {printers.map(p => (
              <div key={p.id} className="flex items-center justify-between border rounded-lg px-4 py-3">
                <div>
                  <p className="font-medium text-brand-text">{p.name || 'Unnamed Printer'}</p>
                  <p className="text-xs text-gray-400 font-mono">{p.mac_address}</p>
                  <p className="text-xs text-gray-400 mt-0.5">Last seen: {formatLastSeen(p.last_seen_at)}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                    p.last_seen_at && (Date.now() - new Date(p.last_seen_at)) / 1000 < 120
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}>
                    {p.last_seen_at && (Date.now() - new Date(p.last_seen_at)) / 1000 < 120 ? 'Online' : 'Offline'}
                  </span>
                  <button
                    onClick={() => handleUnclaim(p.id)}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Claim a new printer */}
      <form onSubmit={handleClaim} className="bg-brand-surface rounded-xl shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-800">Claim a Printer</h2>
        <p className="text-sm text-gray-500">
          Power on your ByteOrder printer. Connect your phone to the <strong>ByteOrder-XXXXXX</strong> WiFi network
          and follow the setup steps — your 6-character claim code will be shown on screen.
        </p>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Claim Code</label>
          <input
            value={claimCode}
            onChange={e => setClaimCode(e.target.value.toUpperCase().replace(/[^A-F0-9]/g, ''))}
            maxLength={6}
            placeholder="A1B2C3"
            className="w-full border rounded-lg px-3 py-2 font-mono text-lg tracking-widest uppercase"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Printer Name</label>
          <input
            value={claimName}
            onChange={e => setClaimName(e.target.value)}
            placeholder="Kitchen Printer"
            className="w-full border rounded-lg px-3 py-2"
          />
        </div>

        <button
          type="submit"
          disabled={claiming || claimCode.length !== 6}
          className="bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white font-medium rounded-lg px-6 py-2"
        >
          {claiming ? 'Claiming…' : 'Claim Printer'}
        </button>
      </form>
    </div>
  )
}
