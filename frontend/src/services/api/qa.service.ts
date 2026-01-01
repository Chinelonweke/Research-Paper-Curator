import api from '@/plugins/axios'
import type { QAResponse } from '@/types/api.types'

class QAService {
  async ask(question: string): Promise<QAResponse> {
    const response = await api.post('/api/ask', { question })
    return response.data
  }
}

export default new QAService()
