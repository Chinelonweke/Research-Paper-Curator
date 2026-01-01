<template>
  <v-card class="paper-card" :elevation="hover ? 4 : 2">
    <v-card-title class="d-flex align-start">
      <span class="flex-grow-1 paper-title">{{ paper.title }}</span>
      <v-btn
        v-if="authStore.isAuthenticated"
        icon
        variant="text"
        :color="isSaved ? 'primary' : 'grey'"
        @click.stop="handleBookmarkToggle"
        :loading="saving"
      >
        <v-icon>{{ isSaved ? 'mdi-bookmark' : 'mdi-bookmark-outline' }}</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ isSaved ? 'Remove from collection' : 'Save to collection' }}
        </v-tooltip>
      </v-btn>
    </v-card-title>

    <v-card-subtitle class="d-flex align-center">
      <v-icon size="small" class="mr-1">mdi-account-group</v-icon>
      {{ paper.authors }}
    </v-card-subtitle>

    <v-card-text>
      <p class="text-body-2 mb-4">
        {{ truncatedAbstract }}
        <a
          v-if="isAbstractTruncated"
          href="#"
          class="text-primary"
          @click.prevent="showFullAbstract = true"
        >
          Read more
        </a>
      </p>

      <div class="d-flex align-center flex-wrap ga-2">
        <v-chip
          v-if="paper.category"
          size="small"
          color="primary"
          variant="outlined"
        >
          {{ paper.category }}
        </v-chip>
        <v-chip v-if="paper.published" size="small" variant="outlined">
          <v-icon start size="small">mdi-calendar</v-icon>
          {{ paper.published }}
        </v-chip>
      </div>
    </v-card-text>

    <v-card-actions>
      <v-btn
        v-if="paper.url"
        :href="paper.url"
        target="_blank"
        color="primary"
        variant="text"
      >
        <v-icon start>mdi-file-pdf-box</v-icon>
        View PDF
      </v-btn>
      <v-spacer />
      <v-btn variant="text" @click="showFullAbstract = true">
        Details
      </v-btn>
    </v-card-actions>

    <!-- Full Abstract Dialog -->
    <v-dialog v-model="showFullAbstract" max-width="800">
      <v-card>
        <v-card-title class="d-flex align-center">
          <span class="flex-grow-1">{{ paper.title }}</span>
          <v-btn icon variant="text" @click="showFullAbstract = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-subtitle>{{ paper.authors }}</v-card-subtitle>
        <v-card-text>
          <h4 class="text-subtitle-1 mb-2">Abstract</h4>
          <p class="text-body-1">{{ paper.abstract }}</p>

          <v-divider class="my-4" />

          <div class="d-flex flex-wrap ga-2">
            <v-chip v-if="paper.category" color="primary">
              {{ paper.category }}
            </v-chip>
            <v-chip v-if="paper.published">
              <v-icon start>mdi-calendar</v-icon>
              {{ paper.published }}
            </v-chip>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-btn
            v-if="paper.url"
            :href="paper.url"
            target="_blank"
            color="primary"
          >
            <v-icon start>mdi-file-pdf-box</v-icon>
            View PDF
          </v-btn>
          <v-spacer />
          <v-btn @click="showFullAbstract = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Paper } from '@/types/paper.types'
import { useAuthStore } from '@/stores/auth.store'
import { useCollectionsStore } from '@/stores/collections.store'
import { useUIStore } from '@/stores/ui.store'

const props = defineProps<{
  paper: Paper
}>()

const authStore = useAuthStore()
const collectionsStore = useCollectionsStore()
const uiStore = useUIStore()

const hover = ref(false)
const showFullAbstract = ref(false)
const saving = ref(false)

const MAX_ABSTRACT_LENGTH = 300

const truncatedAbstract = computed(() => {
  if (!props.paper.abstract) return ''
  if (props.paper.abstract.length <= MAX_ABSTRACT_LENGTH) {
    return props.paper.abstract
  }
  return props.paper.abstract.substring(0, MAX_ABSTRACT_LENGTH) + '...'
})

const isAbstractTruncated = computed(() => {
  return props.paper.abstract && props.paper.abstract.length > MAX_ABSTRACT_LENGTH
})

const isSaved = computed(() => {
  return collectionsStore.isPaperSaved(Number(props.paper.id))
})

async function handleBookmarkToggle() {
  saving.value = true
  try {
    if (isSaved.value) {
      const savedPaper = collectionsStore.getSavedPaperByPaperId(Number(props.paper.id))
      if (savedPaper) {
        await collectionsStore.removeSavedPaper(savedPaper.id)
        uiStore.showSuccess('Removed from collection')
      }
    } else {
      await collectionsStore.savePaper(Number(props.paper.id))
      uiStore.showSuccess('Added to collection')
    }
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.paper-card {
  transition: all 0.2s ease;
}

.paper-title {
  line-height: 1.4;
}
</style>
