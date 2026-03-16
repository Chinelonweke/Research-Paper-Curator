<template>
  <v-card
    class="paper-card glass-panel hover-lift rounded-xl border-0 overflow-hidden"
    :elevation="hover ? 8 : 0"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
  >
    <v-card-item class="pb-2">
      <template #append>
        <v-btn
          v-if="authStore.isAuthenticated"
          icon
          variant="tonal"
          :color="isSaved ? 'primary' : 'grey'"
          size="small"
          @click.stop="handleBookmarkToggle"
          :loading="saving"
        >
          <v-icon>{{ isSaved ? 'mdi-bookmark' : 'mdi-bookmark-outline' }}</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ isSaved ? 'Remove from collection' : 'Save to collection' }}
          </v-tooltip>
        </v-btn>
      </template>
      <v-card-title class="text-h6 font-weight-bold paper-title line-clamp-2" style="white-space: normal; line-height: 1.4;">
        {{ paper.title }}
      </v-card-title>
      <v-card-subtitle class="mt-2 text-primary font-weight-medium d-flex align-center">
        <v-icon size="small" class="mr-1">mdi-account-group</v-icon>
        {{ paper.authors }}
      </v-card-subtitle>
    </v-card-item>

    <v-card-text>
      <p class="text-body-2 text-medium-emphasis mb-4 line-clamp-3">
        {{ truncatedAbstract }}
        <a
          v-if="isAbstractTruncated"
          href="#"
          class="text-primary font-weight-bold text-decoration-none"
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
          variant="tonal"
          class="font-weight-medium"
        >
          {{ paper.category }}
        </v-chip>
        <v-chip
          v-if="paper.published"
          size="small"
          variant="tonal"
          color="secondary"
          class="font-weight-medium"
        >
          <v-icon start size="x-small">mdi-calendar</v-icon>
          {{ paper.published }}
        </v-chip>
      </div>
    </v-card-text>

    <v-divider class="opacity-10" />

    <v-card-actions class="pa-4 pt-3">
      <v-btn
        v-if="paper.url"
        :href="paper.url"
        target="_blank"
        color="primary"
        variant="flat"
        size="small"
        rounded="pill"
        class="px-4"
      >
        <v-icon start size="small">mdi-file-pdf-box</v-icon>
        View PDF
      </v-btn>
      <v-spacer />
      <v-btn
        variant="text"
        size="small"
        color="primary"
        @click="showFullAbstract = true"
        class="font-weight-bold"
      >
        Details
        <v-icon end size="small">mdi-arrow-right</v-icon>
      </v-btn>
    </v-card-actions>

    <!-- Full Abstract Dialog -->
    <v-dialog v-model="showFullAbstract" max-width="800">
      <v-card class="glass-panel rounded-xl border-0">
        <v-card-title class="pa-6 d-flex align-start">
          <span class="flex-grow-1 text-h5 font-weight-bold" style="white-space: normal; line-height: 1.3;">
            {{ paper.title }}
          </span>
          <v-btn icon variant="tonal" size="small" @click="showFullAbstract = false" class="ml-4">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        
        <v-card-subtitle class="px-6 text-primary font-weight-medium h6">
          <v-icon size="small" class="mr-1">mdi-account-group</v-icon>
          {{ paper.authors }}
        </v-card-subtitle>

        <v-card-text class="pa-6">
          <div class="bg-grey-lighten-4 rounded-xl pa-6">
            <h4 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
              <v-icon start size="small" color="primary">mdi-text-subject</v-icon>
              Abstract
            </h4>
            <p class="text-body-1 text-medium-emphasis" style="line-height: 1.6;">
              {{ paper.abstract }}
            </p>
          </div>

          <v-divider class="my-6 opacity-10" />

          <div class="d-flex flex-wrap ga-3">
            <v-chip v-if="paper.category" color="primary" variant="tonal" size="large" class="font-weight-bold">
              {{ paper.category }}
            </v-chip>
            <v-chip v-if="paper.published" variant="tonal" size="large" class="font-weight-bold">
              <v-icon start>mdi-calendar</v-icon>
              {{ paper.published }}
            </v-chip>
          </div>
        </v-card-text>

        <v-divider class="opacity-10" />

        <v-card-actions class="pa-6">
          <v-btn
            v-if="paper.url"
            :href="paper.url"
            target="_blank"
            color="primary"
            variant="flat"
            size="large"
            rounded="pill"
            class="px-8 font-weight-bold"
          >
            <v-icon start>mdi-file-pdf-box</v-icon>
            View Full PDF
          </v-btn>
          <v-spacer />
          <v-btn variant="text" size="large" @click="showFullAbstract = false" class="font-weight-bold">
            Close
          </v-btn>
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
