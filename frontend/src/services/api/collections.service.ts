import api from '@/plugins/axios'
import type { SavedPaper } from '@/types/paper.types'

class CollectionsService {
  async getSavedPapers(): Promise<SavedPaper[]> {
    const response = await api.get('/api/collections/saved')
    return response.data
  }

  async savePaper(paperId: number, notes?: string): Promise<SavedPaper> {
    const response = await api.post('/api/collections/save', {
      paper_id: paperId,
      notes
    })
    return response.data
  }

  async removeSavedPaper(savedPaperId: number): Promise<void> {
    await api.delete(`/api/collections/${savedPaperId}`)
  }

  async updateNotes(savedPaperId: number, notes: string): Promise<SavedPaper> {
    const response = await api.put(`/api/collections/${savedPaperId}/notes`, { notes })
    return response.data
  }
}

export default new CollectionsService()
