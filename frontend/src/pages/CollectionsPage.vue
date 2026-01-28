<template>
  <v-container fluid class="pa-0">
    <v-row class="mb-8 p-4">
      <v-col cols="12" class="d-flex align-center justify-space-between glass-panel rounded-xl pa-6">
        <div class="d-flex align-center">
          <v-avatar color="primary" variant="tonal" size="56" class="mr-4">
            <v-icon size="32">mdi-bookmark</v-icon>
          </v-avatar>
          <div>
            <h1 class="text-h4 font-weight-bold mb-1">My Collections</h1>
            <p class="text-body-1 text-medium-emphasis mb-0">
              Your curated library of research insights
            </p>
          </div>
        </div>
        <v-chip
          v-if="collectionsStore.savedPapers.length"
          color="primary"
          variant="elevated"
          size="large"
          class="font-weight-bold"
        >
          {{ collectionsStore.savedPapers.length }} Papers
        </v-chip>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-row v-if="collectionsStore.error" class="mb-6">
      <v-col cols="12">
        <v-alert
          type="error"
          variant="tonal"
          closable
          @click:close="collectionsStore.clearError"
          class="rounded-lg"
        >
          {{ collectionsStore.error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Loading -->
    <v-row v-if="collectionsStore.loading">
      <v-col cols="12" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" width="6" />
        <p class="mt-4 text-h6 font-weight-medium">Loading your collection...</p>
      </v-col>
    </v-row>

    <!-- Saved Papers List -->
    <v-row v-else-if="collectionsStore.savedPapers.length">
      <v-col
        v-for="savedPaper in collectionsStore.savedPapers"
        :key="savedPaper.id"
        cols="12"
        md="6"
        lg="4"
      >
        <v-card class="glass-panel hover-lift rounded-xl h-100 d-flex flex-column border-0">
          <v-card-item class="pb-2">
            <template #append>
              <v-btn
                icon
                variant="tonal"
                color="error"
                size="small"
                @click="handleRemove(savedPaper.id)"
              >
                <v-icon size="small">mdi-bookmark-remove</v-icon>
                <v-tooltip activator="parent" location="top">Remove</v-tooltip>
              </v-btn>
            </template>
            <v-card-title class="text-h6 font-weight-bold line-clamp-2" style="white-space: normal; line-height: 1.4;">
              {{ savedPaper.paper?.title || `Paper #${savedPaper.paper_id}` }}
            </v-card-title>
            <v-card-subtitle v-if="savedPaper.paper" class="mt-2 text-primary font-weight-medium">
              {{ savedPaper.paper.authors }}
            </v-card-subtitle>
          </v-card-item>

          <v-card-text class="flex-grow-1">
            <p v-if="savedPaper.paper" class="text-body-2 text-medium-emphasis mb-4 line-clamp-3">
              {{ truncateAbstract(savedPaper.paper.abstract) }}
            </p>

            <v-divider class="mb-4 opacity-10" />
            
            <div class="notes-section bg-grey-lighten-4 rounded-lg pa-3">
              <div class="d-flex align-center mb-2">
                <v-icon size="x-small" color="primary" class="mr-2">mdi-note-text</v-icon>
                <span class="text-caption font-weight-bold text-uppercase">My Notes</span>
                <v-spacer />
                <v-btn
                  v-if="!editingNotes[savedPaper.id]"
                  variant="text"
                  size="x-small"
                  color="primary"
                  @click="startEditingNotes(savedPaper.id, savedPaper.notes)"
                >
                  <v-icon start size="x-small">mdi-pencil</v-icon>
                  Edit
                </v-btn>
              </div>

              <template v-if="editingNotes[savedPaper.id]">
                <v-textarea
                  v-model="notesText[savedPaper.id]"
                  placeholder="Add your notes..."
                  rows="2"
                  auto-grow
                  variant="plain"
                  density="compact"
                  hide-details
                  class="text-body-2"
                />
                <div class="d-flex gap-2 mt-2">
                  <v-btn
                    color="primary"
                    size="x-small"
                    variant="flat"
                    @click="saveNotes(savedPaper.id)"
                  >
                    Save
                  </v-btn>
                  <v-btn
                    variant="text"
                    size="x-small"
                    @click="cancelEditingNotes(savedPaper.id)"
                  >
                    Cancel
                  </v-btn>
                </div>
              </template>
              <template v-else>
                <p class="text-body-2 text-medium-emphasis mb-0 italic">
                  {{ savedPaper.notes || 'Capture your thoughts here...' }}
                </p>
              </template>
            </div>
          </v-card-text>

          <v-card-actions class="pa-4 pt-0">
            <div class="text-caption text-medium-emphasis d-flex align-center">
              <v-icon size="x-small" class="mr-1">mdi-calendar</v-icon>
              {{ formatDate(savedPaper.saved_at) }}
            </div>
            <v-spacer />
            <v-btn
              v-if="savedPaper.paper?.url"
              :href="savedPaper.paper.url"
              target="_blank"
              variant="flat"
              color="primary"
              size="small"
              rounded="pill"
            >
              <v-icon start size="small">mdi-file-pdf-box</v-icon>
              Read PDF
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-row v-else justify="center">
      <v-col cols="12" md="8" lg="6" class="text-center py-16">
        <div class="glass-panel rounded-xl pa-12">
          <v-icon size="120" color="grey-lighten-2" class="mb-6">mdi-bookmark-off-outline</v-icon>
          <h2 class="text-h4 font-weight-bold mb-4">Your collection is empty</h2>
          <p class="text-h6 text-medium-emphasis mb-8">
            Start exploring the vast world of research and save the most insightful papers here.
          </p>
          <v-btn
            color="primary"
            size="x-large"
            rounded="pill"
            :to="{ name: 'search' }"
            class="px-8 font-weight-bold shadow-lg"
          >
            <v-icon start>mdi-magnify</v-icon>
            Discover Papers
          </v-btn>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { format } from 'date-fns'
import { useCollectionsStore } from '@/stores/collections.store'
import { useUIStore } from '@/stores/ui.store'

const collectionsStore = useCollectionsStore()
const uiStore = useUIStore()

const editingNotes = reactive<Record<number, boolean>>({})
const notesText = reactive<Record<number, string>>({})

function truncateAbstract(abstract: string, maxLength = 300): string {
  if (!abstract) return ''
  if (abstract.length <= maxLength) return abstract
  return abstract.substring(0, maxLength) + '...'
}

function formatDate(dateStr: string): string {
  return format(new Date(dateStr), 'MMM d, yyyy')
}

function startEditingNotes(id: number, notes?: string) {
  editingNotes[id] = true
  notesText[id] = notes || ''
}

function cancelEditingNotes(id: number) {
  editingNotes[id] = false
}

async function saveNotes(id: number) {
  const success = await collectionsStore.updateNotes(id, notesText[id])
  if (success) {
    editingNotes[id] = false
    uiStore.showSuccess('Notes saved')
  }
}

async function handleRemove(id: number) {
  const success = await collectionsStore.removeSavedPaper(id)
  if (success) {
    uiStore.showSuccess('Paper removed from collection')
  }
}

onMounted(() => {
  collectionsStore.fetchSavedPapers()
})
</script>
