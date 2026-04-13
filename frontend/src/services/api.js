import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api'
})

export const fetchUpcomingMatches = async ({ days = 3, competitions = '' } = {}) => {
  const params = new URLSearchParams()
  params.set('days', String(days))
  if (competitions.trim()) params.set('competitions', competitions.trim())
  const { data } = await api.get(`/matches/upcoming?${params.toString()}`)
  return data.matches || []
}

export const fetchAnalysis = async (matchId) => {
  const { data } = await api.get(`/analysis/${matchId}`)
  return data
}

export default api
