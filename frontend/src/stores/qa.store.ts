import { defineStore } from 'pinia'
import { ref } from 'vue'
import qaService from '@/services/api/qa.service'

interface HistoryItem {
  question: string
  answer: string
  sources: string[]
  timestamp: Date
}

export const useQAStore = defineStore('qa', () => {
  // State
  const answer = ref<string>('')
  const sources = ref<string[]>([])
  const audioUrl = ref<string | null>(null)
  const loading = ref(false)
  const streaming = ref(false)
  const error = ref<string | null>(null)
  const history = ref<HistoryItem[]>([])

  // Actions
  async function askQuestion(question: string) {
    loading.value = true
    error.value = null
    answer.value = ''
    sources.value = []
    audioUrl.value = null

    try {
      const response = await qaService.ask(question)
      answer.value = response.answer
      sources.value = response.sources
      audioUrl.value = response.audio_url || null

      history.value.unshift({
        question,
        answer: response.answer,
        sources: response.sources,
        timestamp: new Date()
      })

      return response
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to get answer'
      throw e
    } finally {
      loading.value = false
    }
  }

  function appendStreamChunk(chunk: string) {
    answer.value += chunk
  }

  function setStreaming(value: boolean) {
    streaming.value = value
  }

  function setStreamingSources(newSources: string[]) {
    sources.value = newSources
  }

  function clearAnswer() {
    answer.value = ''
    sources.value = []
    audioUrl.value = null
    error.value = null
  }

  function clearError() {
    error.value = null
  }

  return {
    answer,
    sources,
    audioUrl,
    loading,
    streaming,
    error,
    history,
    askQuestion,
    appendStreamChunk,
    setStreaming,
    setStreamingSources,
    clearAnswer,
    clearError
  }
})
