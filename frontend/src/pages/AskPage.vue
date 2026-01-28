<template>
  <v-container fluid class="pa-0">
    <v-row class="mb-8 p-4">
      <v-col cols="12" class="d-flex align-center justify-space-between glass-panel rounded-xl pa-6">
        <div class="d-flex align-center">
          <v-avatar color="primary" variant="tonal" size="56" class="mr-4">
            <v-icon size="32">mdi-comment-question</v-icon>
          </v-avatar>
          <div>
            <h1 class="text-h4 font-weight-bold mb-1">Ask Questions</h1>
            <p class="text-body-1 text-medium-emphasis mb-0">
              Get AI-powered answers based on research papers
            </p>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Question Input -->
    <v-row justify="center" class="mb-8 px-4">
      <v-col cols="12" lg="10" xl="8">
        <v-card class="glass-panel rounded-xl border-0 pa-2">
          <v-card-text>
            <v-textarea
              v-model="question"
              label="What would you like to know?"
              placeholder="e.g., What are the key innovations in transformer architecture?"
              rows="3"
              auto-grow
              variant="plain"
              class="text-h6"
              :disabled="qaStore.loading || qaStore.streaming"
              hide-details
            />

            <v-divider class="my-4 opacity-10" />

            <div class="d-flex align-center flex-wrap gap-3">
              <v-btn
                color="primary"
                size="large"
                rounded="pill"
                class="px-8 font-weight-bold"
                :loading="qaStore.loading"
                :disabled="!question.trim() || qaStore.streaming"
                @click="handleAsk"
              >
                <v-icon start>mdi-send</v-icon>
                Get Answer
              </v-btn>

              <v-btn
                v-if="wsConnected"
                color="secondary"
                size="large"
                variant="tonal"
                rounded="pill"
                class="px-8 font-weight-bold"
                :loading="qaStore.streaming"
                :disabled="!question.trim() || qaStore.loading"
                @click="handleStreamingAsk"
              >
                <v-icon start>mdi-lightning-bolt</v-icon>
                Stream
              </v-btn>

              <v-spacer />

              <v-chip
                v-if="wsConnected"
                color="success"
                variant="flat"
                size="small"
                class="font-weight-bold"
              >
                <v-icon start size="small">mdi-wifi</v-icon>
                LIVE
              </v-chip>
              <v-chip
                v-else
                color="grey"
                variant="flat"
                size="small"
                class="font-weight-bold"
              >
                <v-icon start size="small">mdi-wifi-off</v-icon>
                OFFLINE
              </v-chip>
            </div>

            <div class="d-flex align-center mt-4 text-caption text-medium-emphasis">
              <v-icon size="x-small" class="mr-1">mdi-information-outline</v-icon>
              Generated based on indexed papers. May take 30-60s.
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-row v-if="qaStore.error" justify="center" class="mb-6 px-4">
      <v-col cols="12" lg="10" xl="8">
        <v-alert
          type="error"
          variant="tonal"
          closable
          @click:close="qaStore.clearError"
          class="rounded-lg shadow-sm"
        >
          {{ qaStore.error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Answer Display -->
    <v-row v-if="qaStore.answer || qaStore.streaming" justify="center" class="mb-8 px-4">
      <v-col cols="12" lg="10" xl="8">
        <v-card class="glass-panel rounded-xl border-0 overflow-hidden">
          <div class="bg-grey-lighten-4 px-6 py-4 d-flex align-center border-b">
            <v-icon color="primary" class="mr-2">mdi-auto-fix</v-icon>
            <span class="text-subtitle-1 font-weight-bold text-primary">AI Synthesis</span>
            <v-spacer />
            <v-progress-circular
              v-if="qaStore.streaming"
              indeterminate
              size="18"
              width="2"
              color="primary"
            />
          </div>
          <v-card-text class="pa-8">
            <div
              class="answer-content text-body-1"
              v-html="formattedAnswer"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row justify="center" class="px-4">
      <v-col cols="12" lg="10" xl="8">
        <v-row>
          <!-- Sources -->
          <v-col v-if="qaStore.sources.length" cols="12" md="6">
            <v-card class="glass-panel rounded-xl h-100 border-0">
              <v-card-title class="px-6 pt-6 font-weight-bold d-flex align-center">
                <v-icon color="primary" class="mr-2" size="small">mdi-book-multiple</v-icon>
                Sources
                <v-chip size="x-small" class="ml-2" color="primary" variant="tonal">
                  {{ qaStore.sources.length }}
                </v-chip>
              </v-card-title>
              <v-card-text class="px-4 pb-6 mt-2">
                <v-list bg-color="transparent">
                  <v-list-item
                    v-for="(source, index) in qaStore.sources"
                    :key="index"
                    class="rounded-lg mb-1"
                  >
                    <template #prepend>
                      <v-icon color="primary" size="small">mdi-file-document-outline</v-icon>
                    </template>
                    <v-list-item-title class="text-body-2">{{ source }}</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Audio Player if available -->
          <v-col v-if="qaStore.audioUrl" cols="12" md="6">
            <v-card class="glass-panel rounded-xl h-100 border-0">
              <v-card-title class="px-6 pt-6 font-weight-bold">
                <v-icon color="primary" class="mr-2" size="small">mdi-volume-high</v-icon>
                Listen
              </v-card-title>
              <v-card-text class="pa-6">
                <audio controls :src="qaStore.audioUrl" class="w-100 custom-audio" />
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Recent Questions -->
          <v-col v-if="qaStore.history.length" cols="12">
            <v-card class="glass-panel rounded-xl border-0 mb-8">
              <v-card-title class="px-6 pt-6 font-weight-bold">
                <v-icon color="secondary" class="mr-2" size="small">mdi-history</v-icon>
                Recent Explorations
              </v-card-title>
              <v-card-text class="px-4 pb-4 mt-2">
                <v-row>
                  <v-col
                    v-for="(item, index) in qaStore.history.slice(0, 4)"
                    :key="index"
                    cols="12"
                    sm="6"
                  >
                    <v-list-item
                      @click="loadHistoryItem(item)"
                      class="hover-lift glass-panel rounded-xl mb-2 cursor-pointer border-0"
                    >
                      <template #prepend>
                        <v-avatar color="secondary" variant="tonal" size="32" class="mr-2">
                          <v-icon size="16">mdi-comment-question-outline</v-icon>
                        </v-avatar>
                      </template>
                      <v-list-item-title class="text-body-2 font-weight-medium line-clamp-1">
                        {{ item.question }}
                      </v-list-item-title>
                      <v-list-item-subtitle class="text-caption">
                        {{ formatDate(item.timestamp) }}
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { format } from 'date-fns'
import { useQAStore } from '@/stores/qa.store'
import wsService from '@/services/websocket.service'

const qaStore = useQAStore()
const question = ref('')

const wsConnected = computed(() => wsService.connected.value)

const formattedAnswer = computed(() => {
  if (!qaStore.answer) return ''
  // Workaround for TypeScript issue with marked return type
  const markedFn = marked as unknown as (src: string) => string
  const rawHtml = markedFn(qaStore.answer)
  // Use strict DOMPurify config to prevent XSS
  const purifyConfig = {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'strike', 'del',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li',
      'blockquote', 'code', 'pre',
      'a', 'img',
      'table', 'thead', 'tbody', 'tr', 'th', 'td'
    ],
    ALLOWED_ATTR: [
      'href', 'title', 'target',
      'src', 'alt', 'width', 'height',
      'class'
    ],
    ALLOW_DATA_ATTR: false,
    SANITIZE_DOM: true,
    // Force all links to open in new tab with rel="noopener noreferrer"
    FORCE_BODY: true
  }
  return DOMPurify.sanitize(rawHtml, purifyConfig) as string
})

async function handleAsk() {
  if (!question.value.trim()) return
  await qaStore.askQuestion(question.value)
}

function handleStreamingAsk() {
  if (!question.value.trim()) return
  qaStore.clearAnswer()
  qaStore.setStreaming(true)
  wsService.askStreaming(question.value)
}

function loadHistoryItem(item: { question: string; answer: string }) {
  question.value = item.question
  qaStore.answer = item.answer
}

function formatDate(date: Date): string {
  return format(date, 'MMM d, yyyy h:mm a')
}

// WebSocket handlers
function handleStatus(data: { message: string }) {
  console.log('Status:', data.message)
}

function handleAnswerChunk(data: { chunk: string }) {
  qaStore.appendStreamChunk(data.chunk)
}

function handleAnswerComplete(data: { sources?: string[] }) {
  qaStore.setStreaming(false)
  if (data.sources) {
    qaStore.setStreamingSources(data.sources)
  }
}

function handleSearchResults(data: { results: any[] }) {
  console.log('Found sources:', data.results.length)
}

onMounted(() => {
  // Connect WebSocket
  wsService.connect()

  // Register handlers
  wsService.on('status', handleStatus)
  wsService.on('answer_chunk', handleAnswerChunk)
  wsService.on('answer_complete', handleAnswerComplete)
  wsService.on('search_results', handleSearchResults)
})

onUnmounted(() => {
  // Unregister handlers
  wsService.off('status', handleStatus)
  wsService.off('answer_chunk', handleAnswerChunk)
  wsService.off('answer_complete', handleAnswerComplete)
  wsService.off('search_results', handleSearchResults)
})
</script>

<style scoped>
.answer-content {
  line-height: 1.8;
}
.answer-content :deep(p) {
  margin-bottom: 1em;
}
.answer-content :deep(h1),
.answer-content :deep(h2),
.answer-content :deep(h3) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}
.answer-content :deep(ul),
.answer-content :deep(ol) {
  padding-left: 1.5em;
  margin-bottom: 1em;
}
.answer-content :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 0.2em 0.4em;
  border-radius: 4px;
}
.cursor-pointer {
  cursor: pointer;
}
</style>
