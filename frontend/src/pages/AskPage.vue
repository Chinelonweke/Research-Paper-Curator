<template>
  <div>
    <v-row class="mb-6">
      <v-col cols="12">
        <h1 class="text-h4 mb-2">
          <v-icon class="mr-2">mdi-comment-question</v-icon>
          Ask Questions
        </h1>
        <p class="text-body-1 text-medium-emphasis">
          Get AI-powered answers based on research papers
        </p>
      </v-col>
    </v-row>

    <!-- Question Input -->
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card>
          <v-card-text>
            <v-textarea
              v-model="question"
              label="Your question"
              placeholder="e.g., What are the key innovations in transformer architecture?"
              rows="3"
              auto-grow
              :disabled="qaStore.loading || qaStore.streaming"
            />

            <div class="d-flex align-center flex-wrap gap-2 mt-4">
              <v-btn
                color="primary"
                size="large"
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
                :loading="qaStore.streaming"
                :disabled="!question.trim() || qaStore.loading"
                @click="handleStreamingAsk"
              >
                <v-icon start>mdi-lightning-bolt</v-icon>
                Stream Answer
              </v-btn>

              <v-spacer />

              <v-chip
                v-if="wsConnected"
                color="success"
                size="small"
              >
                <v-icon start size="small">mdi-wifi</v-icon>
                Live
              </v-chip>
              <v-chip
                v-else
                color="grey"
                size="small"
              >
                <v-icon start size="small">mdi-wifi-off</v-icon>
                Offline
              </v-chip>
            </div>

            <p class="text-body-2 text-medium-emphasis mt-4">
              <v-icon size="small">mdi-information</v-icon>
              Answers are generated based on indexed research papers and may take 30-60 seconds.
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-row v-if="qaStore.error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="qaStore.clearError">
          {{ qaStore.error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Answer Display -->
    <v-row v-if="qaStore.answer || qaStore.streaming">
      <v-col cols="12">
        <v-card>
          <v-card-title class="bg-primary text-white d-flex align-center">
            <v-icon class="mr-2">mdi-lightbulb</v-icon>
            Answer
            <v-progress-circular
              v-if="qaStore.streaming"
              indeterminate
              size="20"
              width="2"
              class="ml-4"
            />
          </v-card-title>
          <v-card-text class="pa-6">
            <div
              class="answer-content text-body-1"
              v-html="formattedAnswer"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Sources -->
    <v-row v-if="qaStore.sources.length">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-book-multiple</v-icon>
            Sources ({{ qaStore.sources.length }})
          </v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="(source, index) in qaStore.sources"
                :key="index"
              >
                <template #prepend>
                  <v-icon color="primary">mdi-file-document</v-icon>
                </template>
                <v-list-item-title>{{ source }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Audio Player -->
    <v-row v-if="qaStore.audioUrl">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-volume-high</v-icon>
            Listen to Answer
          </v-card-title>
          <v-card-text>
            <audio controls :src="qaStore.audioUrl" class="w-100" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent Questions -->
    <v-row v-if="qaStore.history.length" class="mt-6">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-history</v-icon>
            Recent Questions
          </v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="(item, index) in qaStore.history.slice(0, 5)"
                :key="index"
                @click="loadHistoryItem(item)"
                class="cursor-pointer"
              >
                <template #prepend>
                  <v-icon color="secondary">mdi-comment-question-outline</v-icon>
                </template>
                <v-list-item-title>{{ item.question }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ formatDate(item.timestamp) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import { format } from 'date-fns'
import { useQAStore } from '@/stores/qa.store'
import wsService from '@/services/websocket.service'

const qaStore = useQAStore()
const question = ref('')

const wsConnected = computed(() => wsService.connected.value)

const formattedAnswer = computed(() => {
  if (!qaStore.answer) return ''
  return marked(qaStore.answer)
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
