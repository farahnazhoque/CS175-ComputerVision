import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

export default function Viewer() {
  const [gaussianResults, setGaussianResults] = useState([])
  const [sortOrder, setSortOrder] = useState('date') // 'date' or 'name'
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchGaussianResults()
  }, [])

  const fetchGaussianResults = async () => {
    try {
      const response = await fetch('/api/gaussian-results')
      if (!response.ok) {
        throw new Error('Failed to fetch results')
      }
      const data = await response.json()
      setGaussianResults(data)
      setIsLoading(false)
    } catch (err) {
      setError(err.message)
      setIsLoading(false)
    }
  }

  const sortResults = (results) => {
    return [...results].sort((a, b) => {
      if (sortOrder === 'date') {
        return new Date(b.createdAt) - new Date(a.createdAt)
      }
      return a.name.localeCompare(b.name)
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <div className="text-lg text-gray-600">Loading...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center text-red-600">
          Error: {error}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white shadow-sm rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Generated Gaussians
              </h2>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option value="date">Sort by Date</option>
                <option value="name">Sort by Name</option>
              </select>
            </div>

            <div className="space-y-4">
              {sortResults(gaussianResults).map((result) => (
                <Link
                  key={result.id}
                  to={`/gaussian/${result.id}`}
                  className="block hover:bg-gray-50"
                >
                  <div className="border rounded-lg p-4 transition duration-150 ease-in-out">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">
                          {result.name}
                        </h3>
                        <p className="text-sm text-gray-500">
                          Created: {new Date(result.createdAt).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-indigo-600">
                        View Details →
                      </div>
                    </div>
                  </div>
                </Link>
              ))}

              {gaussianResults.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No Gaussian results found
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
