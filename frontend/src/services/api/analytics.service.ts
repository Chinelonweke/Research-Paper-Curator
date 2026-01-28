import api from '@/plugins/axios'

export interface SearchLogEntry {
  id: number
  query: string
  results_count: number
  search_type?: string
  timestamp: string
}

export interface TrendingQuery {
  query: string
  count: number
}

export interface SearchTypeStat {
  search_type: string
  count: number
}

export interface SearchStats {
  total_searches: number
  avg_results: number
  min_results: number
  max_results: number
  search_types: SearchTypeStat[]
}

export interface PersonalPatterns {
  daily_counts: { date: string; count: number }[]
  top_queries: TrendingQuery[]
  avg_results: number
  total_searches: number
}

class AnalyticsService {
  async getSearchHistory(limit = 50, offset = 0): Promise<SearchLogEntry[]> {
    const response = await api.get('/api/analytics/searches', { params: { limit, offset } })
    return response.data
  }

  async getTrending(days = 7, limit = 10): Promise<TrendingQuery[]> {
    const response = await api.get('/api/analytics/trending', { params: { days, limit } })
    return response.data
  }

  async getStats(): Promise<SearchStats> {
    const response = await api.get('/api/analytics/stats')
    return response.data
  }

  async getPatterns(days = 30, limit = 5): Promise<PersonalPatterns> {
    const response = await api.get('/api/analytics/patterns', { params: { days, limit } })
    return response.data
  }
}

export default new AnalyticsService()
