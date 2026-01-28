<template>
  <v-container fluid class="pa-0">
    <v-row class="mb-8 p-4">
      <v-col cols="12" class="d-flex align-center justify-space-between glass-panel rounded-xl pa-6">
        <div class="d-flex align-center">
          <v-avatar color="black" variant="tonal" size="56" class="mr-4">
            <v-icon size="32">mdi-history</v-icon>
          </v-avatar>
          <div>
            <h1 class="text-h4 font-weight-bold mb-1">Search History</h1>
            <p class="text-body-1 text-medium-emphasis mb-0">
              Review your past explorations and search insights
            </p>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Loading State -->
    <v-row v-if="loading" class="px-4">
      <v-col cols="12" class="text-center py-12">
        <v-progress-circular indeterminate color="black" size="64" width="6" />
        <p class="mt-4 text-h6 font-weight-medium">Retrieving your archives...</p>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-row v-if="error" class="mb-6 px-4">
      <v-col cols="12">
        <v-alert
          type="error"
          variant="tonal"
          closable
          class="rounded-lg shadow-sm"
        >
          {{ error }}
        </v-alert>
      </v-col>
    </v-row>

    <template v-if="!loading && searchHistory.length">
      <!-- History List -->
      <v-row class="mb-8 px-4">
        <v-col cols="12">
          <v-card class="glass-panel rounded-xl border-0 overflow-hidden">
            <v-card-title class="px-6 pt-6 font-weight-bold d-flex align-center">
              <v-icon color="black" class="mr-2" size="small">mdi-clock-outline</v-icon>
              Recent Searches
            </v-card-title>
            <v-card-text class="pa-4">
              <v-list bg-color="transparent">
                <v-list-item
                  v-for="item in searchHistory"
                  :key="item.id"
                  class="rounded-xl mb-2 hover-lift border-0 px-4 cursor-pointer"
                  @click="navigateToSearch(item.query, item.search_type)"
                >
                  <template #prepend>
                    <v-avatar color="black" variant="tonal" size="40" class="mr-4">
                      <v-icon size="20">mdi-magnify</v-icon>
                    </v-avatar>
                  </template>
                  
                  <v-list-item-title class="text-h6 font-weight-bold">{{ item.query }}</v-list-item-title>
                  <v-list-item-subtitle class="d-flex align-center flex-wrap gap-2 mt-1">
                    <span class="text-caption font-weight-medium">{{ formatDateString(item.timestamp) }}</span>
                    <v-chip size="x-small" variant="tonal" color="black" class="font-weight-bold">
                      {{ item.results_count }} results
                    </v-chip>
                    <v-chip size="x-small" variant="flat" color="grey-lighten-3" v-if="item.search_type" class="font-weight-bold text-uppercase">
                      {{ item.search_type }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Analytics Section -->
      <v-row v-if="stats" class="mb-8 px-4">
        <v-col cols="12" md="6">
          <v-card class="glass-panel rounded-xl border-0 h-100 pa-2">
            <v-card-title class="px-4 pt-4 font-weight-bold">
              <v-icon color="black" class="mr-2" size="small">mdi-chart-box-outline</v-icon>
              Result Analytics
            </v-card-title>
            <v-card-text class="mt-4">
              <div class="d-flex flex-wrap gap-2 mb-6">
                <v-chip color="black" variant="elevated" class="font-weight-bold">{{ stats.total_searches }} searches</v-chip>
                <v-chip variant="tonal" class="font-weight-bold">Avg: {{ stats.avg_results }}</v-chip>
                <v-chip variant="tonal" class="font-weight-bold">Min: {{ stats.min_results }}</v-chip>
                <v-chip variant="tonal" class="font-weight-bold">Max: {{ stats.max_results }}</v-chip>
              </div>
              
              <v-divider class="my-4 opacity-10" />
              
              <div v-if="stats.search_types.length">
                <div class="text-overline font-weight-black mb-2 opacity-60">Distribution by Type</div>
                <v-list bg-color="transparent" density="compact">
                  <v-list-item
                    v-for="type in stats.search_types"
                    :key="type.search_type"
                    class="rounded-lg mb-1"
                  >
                    <template #prepend>
                      <v-icon size="small" class="mr-2">mdi-rhombus-medium-outline</v-icon>
                    </template>
                    <v-list-item-title class="text-body-2 font-weight-bold">{{ type.search_type }}</v-list-item-title>
                    <template #append>
                      <v-chip size="x-small" variant="flat" color="black" class="font-weight-bold">{{ type.count }}</v-chip>
                    </template>
                  </v-list-item>
                </v-list>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <v-card class="glass-panel rounded-xl border-0 h-100 pa-2">
            <v-card-title class="px-4 pt-4 font-weight-bold">
              <v-icon color="black" class="mr-2" size="small">mdi-trending-up</v-icon>
              Trending Topics
            </v-card-title>
            <v-card-text class="mt-4">
              <v-list bg-color="transparent" density="compact" v-if="trending.length">
                <v-list-item
                  v-for="item in trending"
                  :key="item.query"
                  class="rounded-lg mb-1 hover-lift cursor-pointer"
                  @click="navigateToSearch(item.query)"
                >
                  <template #prepend>
                    <v-icon size="small" class="mr-2" color="black">mdi-tag-outline</v-icon>
                  </template>
                  <v-list-item-title class="text-body-2 font-weight-bold">{{ item.query }}</v-list-item-title>
                  <template #append>
                    <v-chip size="x-small" variant="tonal" class="font-weight-bold">{{ item.count }}</v-chip>
                  </template>
                </v-list-item>
              </v-list>
              <div v-else class="text-body-2 text-medium-emphasis text-center py-8">
                The community is quiet. Check back later.
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-row v-if="patterns" class="mb-12 px-4">
        <v-col cols="12">
          <v-card class="glass-panel rounded-xl border-0 pa-4">
            <v-card-title class="font-weight-bold">
              <v-icon color="black" class="mr-2" size="small">mdi-account-star-outline</v-icon>
              Your Search Patterns
            </v-card-title>
            <v-card-text>
              <div class="d-flex flex-wrap gap-2 mb-6">
                <v-chip color="black" variant="flat" class="font-weight-bold">{{ patterns.total_searches }} total exploratons</v-chip>
                <v-chip variant="tonal" class="font-weight-bold">Personal Avg: {{ patterns.avg_results }}</v-chip>
              </div>

              <div class="text-overline font-weight-black mb-2 opacity-60">Top Consulted Queries</div>
              <v-row>
                <v-col
                  v-for="item in patterns.top_queries"
                  :key="item.query"
                  cols="12"
                  sm="6"
                  md="4"
                >
                  <v-list-item
                    class="glass-panel rounded-xl mb-2 hover-lift border-0 cursor-pointer"
                    @click="navigateToSearch(item.query)"
                  >
                    <template #prepend>
                      <v-icon size="small" class="mr-2">mdi-history</v-icon>
                    </template>
                    <v-list-item-title class="text-body-2 font-weight-bold">{{ item.query }}</v-list-item-title>
                    <template #append>
                      <v-chip size="x-small" variant="flat" color="black" class="font-weight-bold">{{ item.count }}</v-chip>
                    </template>
                  </v-list-item>
                </v-col>
              </v-row>
              
              <div v-if="!patterns.top_queries.length" class="text-body-2 text-medium-emphasis text-center py-8">
                No repeated queries yet.
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <!-- Empty State -->
    <v-row v-if="!loading && !searchHistory.length" justify="center" class="px-4">
      <v-col cols="12" md="8" lg="6" class="text-center py-16">
        <div class="glass-panel rounded-xl pa-12">
          <v-icon size="120" color="grey-lighten-2" class="mb-6">mdi-history-off</v-icon>
          <h2 class="text-h4 font-weight-bold mb-4">No history found</h2>
          <p class="text-h6 text-medium-emphasis mb-8">
            Your journey of discovery hasn't left a mark yet. Start asking questions or browsing papers to build your history.
          </p>
          <v-btn
            color="black"
            size="x-large"
            rounded="pill"
            class="px-8 font-weight-bold shadow-lg"
            :to="{ name: 'ask' }"
          >
            <v-icon start>mdi-comment-question</v-icon>
            Ask First Question
          </v-btn>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { format } from 'date-fns'
import analyticsService, {
  SearchLogEntry,
  SearchStats,
  TrendingQuery,
  PersonalPatterns
} from '@/services/api/analytics.service'

const router = useRouter()
const loading = ref(false)
const error = ref<string | null>(null)
const searchHistory = ref<SearchLogEntry[]>([])
const stats = ref<SearchStats | null>(null)
const trending = ref<TrendingQuery[]>([])
const patterns = ref<PersonalPatterns | null>(null)

function formatDateString(dateStr: string): string {
  return format(new Date(dateStr), 'MMM d, yyyy h:mm a')
}

function navigateToSearch(query: string, type?: string) {
  router.push({
    name: 'search',
    query: {
      q: query,
      type: type || 'hybrid'
    }
  })
}

async function loadAnalytics() {
  loading.value = true
  error.value = null
  try {
    const [history, statsResponse, trendingResponse, patternsResponse] = await Promise.all([
      analyticsService.getSearchHistory(),
      analyticsService.getStats(),
      analyticsService.getTrending(),
      analyticsService.getPatterns()
    ])
    searchHistory.value = history
    stats.value = statsResponse
    trending.value = trendingResponse
    patterns.value = patternsResponse
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to load search analytics'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAnalytics()
})
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
</style>
