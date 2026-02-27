import { useState, useEffect } from 'react'
import api from '../lib/api'

export default function MenuManagement() {
  const [categories, setCategories] = useState([])
  const [ingredients, setIngredients] = useState([])
  const [selected, setSelected] = useState(null) // selected category
  const [editingItem, setEditingItem] = useState(null)
  const [newCatName, setNewCatName] = useState('')
  const [newItemName, setNewItemName] = useState('')
  const [newItemDesc, setNewItemDesc] = useState('')

  async function load() {
    const [cats, ings] = await Promise.all([
      api.get('/menu/categories?active_only=false'),
      api.get('/menu/ingredients'),
    ])
    setCategories(cats.data)
    setIngredients(ings.data)
    if (selected) {
      const fresh = cats.data.find(c => c.id === selected.id)
      setSelected(fresh || null)
    }
  }

  useEffect(() => { load() }, [])

  async function addCategory() {
    if (!newCatName.trim()) return
    await api.post('/menu/categories', { name: newCatName, sort_order: categories.length })
    setNewCatName('')
    load()
  }

  async function toggleCategory(cat) {
    await api.put(`/menu/categories/${cat.id}`, { ...cat, active: !cat.active })
    load()
  }

  async function addItem() {
    if (!newItemName.trim() || !selected) return
    await api.post('/menu/items', {
      category_id: selected.id,
      name: newItemName,
      description: newItemDesc,
      sort_order: selected.items?.length || 0,
    })
    setNewItemName('')
    setNewItemDesc('')
    load()
  }

  async function toggleItem(item) {
    await api.put(`/menu/items/${item.id}`, { ...item, active: !item.active })
    load()
  }

  async function deleteItem(item) {
    if (!confirm(`Delete "${item.name}"?`)) return
    await api.delete(`/menu/items/${item.id}`)
    load()
  }

  async function toggleIngredient(item, ingId, currently) {
    if (currently !== undefined) {
      await api.delete(`/menu/items/${item.id}/ingredients/${ingId}`)
    } else {
      await api.post(`/menu/items/${item.id}/ingredients`, { ingredient_id: ingId, is_default: true })
    }
    load()
  }

  return (
    <div className="flex gap-6 h-full">
      {/* Categories panel */}
      <div className="w-56 shrink-0">
        <h2 className="text-lg font-bold text-gray-900 mb-3">Categories</h2>
        <div className="space-y-1 mb-4">
          {categories.map(cat => (
            <div
              key={cat.id}
              className={`flex items-center justify-between rounded-lg px-3 py-2 cursor-pointer ${
                selected?.id === cat.id ? 'bg-orange-100 text-orange-800' : 'hover:bg-gray-100'
              }`}
              onClick={() => setSelected(cat)}
            >
              <span className={`text-sm font-medium ${!cat.active ? 'line-through text-gray-400' : ''}`}>
                {cat.name}
              </span>
              <button
                onClick={e => { e.stopPropagation(); toggleCategory(cat) }}
                className="text-xs text-gray-400 hover:text-gray-700"
              >
                {cat.active ? 'Hide' : 'Show'}
              </button>
            </div>
          ))}
        </div>
        <div className="flex gap-1">
          <input
            value={newCatName}
            onChange={e => setNewCatName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addCategory()}
            placeholder="New category"
            className="flex-1 min-w-0 border rounded px-2 py-1 text-sm"
          />
          <button onClick={addCategory} className="bg-orange-600 text-white rounded px-2 py-1 text-sm">+</button>
        </div>
      </div>

      {/* Items panel */}
      <div className="flex-1">
        {!selected ? (
          <p className="text-gray-400 mt-8 text-center">Select a category</p>
        ) : (
          <>
            <h2 className="text-lg font-bold text-gray-900 mb-3">{selected.name} — Items</h2>
            <div className="space-y-3 mb-6">
              {selected.items?.map(item => (
                <div key={item.id} className="bg-white rounded-lg shadow p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <span className={`font-medium ${!item.active ? 'line-through text-gray-400' : ''}`}>
                        {item.name}
                      </span>
                      {item.description && (
                        <p className="text-xs text-gray-500">{item.description}</p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => toggleItem(item)} className="text-xs text-gray-500 hover:text-gray-800">
                        {item.active ? 'Hide' : 'Show'}
                      </button>
                      <button onClick={() => deleteItem(item)} className="text-xs text-red-500 hover:text-red-700">
                        Delete
                      </button>
                    </div>
                  </div>

                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-1">Ingredients</p>
                    <div className="flex flex-wrap gap-2">
                      {ingredients.map(ing => {
                        const linked = item.item_ingredients?.find(ii => ii.ingredient.id === ing.id)
                        return (
                          <button
                            key={ing.id}
                            onClick={() => toggleIngredient(item, ing.id, linked)}
                            className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                              linked
                                ? 'bg-orange-600 text-white border-orange-600'
                                : 'bg-white text-gray-600 border-gray-300 hover:border-orange-400'
                            }`}
                          >
                            {ing.name}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Add item to {selected.name}</h3>
              <div className="flex gap-2">
                <input
                  value={newItemName}
                  onChange={e => setNewItemName(e.target.value)}
                  placeholder="Item name"
                  className="flex-1 border rounded px-3 py-2 text-sm"
                />
                <input
                  value={newItemDesc}
                  onChange={e => setNewItemDesc(e.target.value)}
                  placeholder="Description (optional)"
                  className="flex-1 border rounded px-3 py-2 text-sm"
                />
                <button
                  onClick={addItem}
                  className="bg-orange-600 text-white rounded px-4 py-2 text-sm font-medium"
                >
                  Add
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
