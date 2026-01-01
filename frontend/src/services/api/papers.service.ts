import api from '@/plugins/axios'
import type { SearchRequest, SearchResponse, PaperListResponse, StatsResponse } from '@/types'

class PapersService {
  async listPapers(skip = 0, limit = 50): Promise<PaperListResponse> {
    const response = await api.get('/api/papers', { params: { skip, limit } })
    return response.data
  }

  async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await api.post('/api/papers/search', request)
    return response.data
  }

  async getStats(): Promise<StatsResponse> {
    const response = await api.get('/api/papers/stats')
    return response.data
  }
}

export default new PapersService()
