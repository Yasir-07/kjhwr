const cache = new Map()

// One request per cutoff; repeat choices come from memory.
export function fetchComparison(cutoff, signal) {
  if (cache.has(cutoff)) return Promise.resolve(cache.get(cutoff))

  return fetch(`/api/comparison?cutoff=${encodeURIComponent(cutoff)}`, { signal })
    .then((res) => {
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      return res.json()
    })
    .then((data) => {
      cache.set(cutoff, data)
      return data
    })
}
