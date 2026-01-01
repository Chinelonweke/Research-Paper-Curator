import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SavedPaper } from '@/types/paper.types'
import collectionsService from '@/services/api/collections.service'

export const useCollectionsStore = defineStore('collections', () => {
  // State
  const savedPapers = ref<SavedPaper[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const savedPaperIds = computed(() =>
    new Set(savedPapers.value.map(sp => sp.paper_id))
  )

  // Actions
  async function fetchSavedPapers() {
    loading.value = true
    error.value = null
    try {
      savedPapers.value = await collectionsService.getSavedPapers()
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to fetch saved papers'
    } finally {
      loading.value = false
    }
  }

  async function savePaper(paperId: number, notes?: string) {
    try {
      const saved = await collectionsService.savePaper(paperId, notes)
      savedPapers.value.push(saved)
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to save paper'
      return false
    }
  }

  async function removeSavedPaper(savedPaperId: number) {
    try {
      await collectionsService.removeSavedPaper(savedPaperId)
      savedPapers.value = savedPapers.value.filter(sp => sp.id !== savedPaperId)
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to remove paper'
      return false
    }
  }

  async function updateNotes(savedPaperId: number, notes: string) {
    try {
      const updated = await collectionsService.updateNotes(savedPaperId, notes)
      const index = savedPapers.value.findIndex(sp => sp.id === savedPaperId)
      if (index !== -1) {
        savedPapers.value[index] = updated
      }
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to update notes'
      return false
    }
  }

  function isPaperSaved(paperId: number): boolean {
    return savedPaperIds.value.has(paperId)
  }

  function getSavedPaperByPaperId(paperId: number): SavedPaper | undefined {
    return savedPapers.value.find(sp => sp.paper_id === paperId)
  }

  function clearError() {
    error.value = null
  }

  return {
    savedPapers,
    loading,
    error,
    savedPaperIds,
    fetchSavedPapers,
    savePaper,
    removeSavedPaper,
    updateNotes,
    isPaperSaved,
    getSavedPaperByPaperId,
    clearError
  }
})
