import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Paper, SearchRequest } from '@/types/paper.types'
import papersService from '@/services/api/papers.service'

export const usePapersStore = defineStore('papers', () => {
  // State
  const papers = ref<Paper[]>([])
  const currentPaper = ref<Paper | null>(null)
  const searchResults = ref<Paper[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const searchMeta = ref<{ source: string; cached: boolean } | null>(null)

  // Actions
  async function fetchPapers(skip = 0, limit = 50) {
    loading.value = true
    error.value = null
    try {
      const response = await papersService.listPapers(skip, limit)
      papers.value = response.papers
      total.value = response.total
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to fetch papers'
    } finally {
      loading.value = false
    }
  }

  async function searchPapers(request: SearchRequest) {
    loading.value = true
    error.value = null
    try {
      const response = await papersService.search(request)
      searchResults.value = response.papers
      searchMeta.value = { source: response.source, cached: response.cached }
      return response
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Search failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  function clearSearch() {
    searchResults.value = []
    searchMeta.value = null
  }

  function clearError() {
    error.value = null
  }

  return {
    papers,
    currentPaper,
    searchResults,
    total,
    loading,
    error,
    searchMeta,
    fetchPapers,
    searchPapers,
    clearSearch,
    clearError
  }
})
