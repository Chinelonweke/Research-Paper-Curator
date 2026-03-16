export interface Paper {
  id: string
  title: string
  authors: string
  abstract: string
  url: string
  published?: string
  category?: string
}

export interface SearchRequest {
  query: string
  limit?: number
  search_type?: 'hybrid' | 'vector' | 'keyword'
}

export interface SearchResponse {
  papers: Paper[]
  total: number
  search_type: string
  source: string
  cached: boolean
}

export interface PaperListResponse {
  papers: Paper[]
  total: number
}

export interface SavedPaper {
  id: number
  user_id: number
  paper_id: number
  saved_at: string
  notes?: string
  paper?: Paper
}
