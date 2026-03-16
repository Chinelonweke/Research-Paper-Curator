export interface QAResponse {
  answer: string
  sources: string[]
  audio_url?: string | null
}

export interface HealthResponse {
  status: string
  database: string
  redis: string
  airflow?: string
}

export interface StatsResponse {
  total_papers: number
  database: string
  redis: string
  status: string
}

export interface SearchHistoryItem {
  id: number
  query: string
  results_count: number
  timestamp: string
  search_type?: string
}

export interface TrendingTopic {
  query: string
  count: number
}
