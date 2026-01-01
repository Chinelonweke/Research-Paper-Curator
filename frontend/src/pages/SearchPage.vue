<template>
  <div>
    <v-row class="mb-6">
      <v-col cols="12">
        <h1 class="text-h4 mb-4">
          <v-icon class="mr-2">mdi-magnify</v-icon>
          Search Papers
        </h1>
      </v-col>
    </v-row>

    <!-- Search Form -->
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="8">
                <v-text-field
                  v-model="query"
                  label="Search query"
                  placeholder="e.g., transformers, attention mechanism, GPT"
                  prepend-inner-icon="mdi-magnify"
                  :loading="papersStore.loading"
                  @keyup.enter="handleSearch"
                  clearable
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="searchType"
                  label="Search type"
                  :items="searchTypes"
                  item-title="label"
                  item-value="value"
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="4">
                <v-slider
                  v-model="limit"
                  label="Results"
                  :min="5"
                  :max="50"
                  :step="5"
                  thumb-label
                />
              </v-col>
              <v-col cols="12" md="8" class="d-flex align-center">
                <v-btn
                  color="primary"
                  size="large"
                  :loading="papersStore.loading"
                  @click="handleSearch"
                >
                  <v-icon start>mdi-magnify</v-icon>
                  Search
                </v-btn>
                <v-btn
                  variant="text"
                  class="ml-2"
                  @click="clearSearch"
                >
                  Clear
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-row v-if="papersStore.error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="papersStore.clearError">
          {{ papersStore.error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Search Meta -->
    <v-row v-if="papersStore.searchMeta && papersStore.searchResults.length">
      <v-col cols="12">
        <div class="d-flex align-center gap-2 mb-4">
          <v-chip color="primary" size="small">
            {{ papersStore.searchResults.length }} results
          </v-chip>
          <v-chip size="small" variant="outlined">
            Source: {{ papersStore.searchMeta.source }}
          </v-chip>
          <v-chip
            v-if="papersStore.searchMeta.cached"
            size="small"
            color="success"
            variant="outlined"
          >
            <v-icon start size="small">mdi-lightning-bolt</v-icon>
            Cached
          </v-chip>
        </div>
      </v-col>
    </v-row>

    <!-- Results -->
    <v-row>
      <v-col
        v-for="paper in papersStore.searchResults"
        :key="paper.id"
        cols="12"
      >
        <PaperCard :paper="paper" />
      </v-col>
    </v-row>

    <!-- No Results -->
    <v-row v-if="searched && !papersStore.loading && !papersStore.searchResults.length">
      <v-col cols="12" class="text-center py-12">
        <v-icon size="64" color="grey">mdi-file-search-outline</v-icon>
        <p class="text-h6 mt-4">No papers found</p>
        <p class="text-body-2 text-medium-emphasis">
          Try adjusting your search terms or search type
        </p>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePapersStore } from '@/stores/papers.store'
import PaperCard from '@/components/papers/PaperCard.vue'

const route = useRoute()
const router = useRouter()
const papersStore = usePapersStore()

const query = ref('')
const searchType = ref<'hybrid' | 'vector' | 'keyword'>('hybrid')
const limit = ref(10)
const searched = ref(false)

const searchTypes = [
  { label: 'Hybrid (Recommended)', value: 'hybrid' },
  { label: 'Vector (Semantic)', value: 'vector' },
  { label: 'Keyword (BM25)', value: 'keyword' }
]

async function handleSearch() {
  if (!query.value.trim()) return

  searched.value = true
  router.replace({ query: { q: query.value, type: searchType.value } })

  await papersStore.searchPapers({
    query: query.value,
    limit: limit.value,
    search_type: searchType.value
  })
}

function clearSearch() {
  query.value = ''
  searched.value = false
  papersStore.clearSearch()
  router.replace({ query: {} })
}

// Load query from URL on mount
onMounted(() => {
  if (route.query.q) {
    query.value = route.query.q as string
    if (route.query.type) {
      searchType.value = route.query.type as 'hybrid' | 'vector' | 'keyword'
    }
    handleSearch()
  }
})

// Watch for route changes
watch(() => route.query.q, (newQuery) => {
  if (newQuery && newQuery !== query.value) {
    query.value = newQuery as string
    handleSearch()
  }
})
</script>
