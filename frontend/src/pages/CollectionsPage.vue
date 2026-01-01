<template>
  <div>
    <v-row class="mb-6">
      <v-col cols="12" class="d-flex align-center justify-space-between">
        <h1 class="text-h4">
          <v-icon class="mr-2">mdi-bookmark</v-icon>
          My Collections
        </h1>
        <v-chip v-if="collectionsStore.savedPapers.length" color="primary">
          {{ collectionsStore.savedPapers.length }} saved
        </v-chip>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-row v-if="collectionsStore.error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="collectionsStore.clearError">
          {{ collectionsStore.error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Loading -->
    <v-row v-if="collectionsStore.loading">
      <v-col cols="12" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <p class="mt-4">Loading saved papers...</p>
      </v-col>
    </v-row>

    <!-- Saved Papers List -->
    <v-row v-else-if="collectionsStore.savedPapers.length">
      <v-col
        v-for="savedPaper in collectionsStore.savedPapers"
        :key="savedPaper.id"
        cols="12"
      >
        <v-card>
          <v-card-title class="d-flex align-center">
            <span class="flex-grow-1">
              {{ savedPaper.paper?.title || `Paper #${savedPaper.paper_id}` }}
            </span>
            <v-btn
              icon
              variant="text"
              color="error"
              @click="handleRemove(savedPaper.id)"
            >
              <v-icon>mdi-bookmark-remove</v-icon>
              <v-tooltip activator="parent" location="top">Remove</v-tooltip>
            </v-btn>
          </v-card-title>

          <v-card-subtitle v-if="savedPaper.paper">
            {{ savedPaper.paper.authors }}
          </v-card-subtitle>

          <v-card-text>
            <p v-if="savedPaper.paper" class="text-body-2 mb-4">
              {{ truncateAbstract(savedPaper.paper.abstract) }}
            </p>

            <!-- Notes Section -->
            <v-divider class="mb-4" />
            <div class="notes-section">
              <div class="d-flex align-center mb-2">
                <v-icon size="small" class="mr-2">mdi-note-text</v-icon>
                <span class="text-subtitle-2">Notes</span>
                <v-spacer />
                <v-btn
                  v-if="!editingNotes[savedPaper.id]"
                  variant="text"
                  size="small"
                  @click="startEditingNotes(savedPaper.id, savedPaper.notes)"
                >
                  <v-icon start size="small">mdi-pencil</v-icon>
                  Edit
                </v-btn>
              </div>

              <template v-if="editingNotes[savedPaper.id]">
                <v-textarea
                  v-model="notesText[savedPaper.id]"
                  placeholder="Add your notes..."
                  rows="3"
                  auto-grow
                  variant="outlined"
                  density="compact"
                />
                <div class="d-flex gap-2 mt-2">
                  <v-btn
                    color="primary"
                    size="small"
                    @click="saveNotes(savedPaper.id)"
                  >
                    Save
                  </v-btn>
                  <v-btn
                    variant="text"
                    size="small"
                    @click="cancelEditingNotes(savedPaper.id)"
                  >
                    Cancel
                  </v-btn>
                </div>
              </template>
              <template v-else>
                <p class="text-body-2 text-medium-emphasis">
                  {{ savedPaper.notes || 'No notes added yet.' }}
                </p>
              </template>
            </div>
          </v-card-text>

          <v-card-actions>
            <v-chip size="small" variant="outlined">
              <v-icon start size="small">mdi-calendar</v-icon>
              Saved {{ formatDate(savedPaper.saved_at) }}
            </v-chip>
            <v-spacer />
            <v-btn
              v-if="savedPaper.paper?.url"
              :href="savedPaper.paper.url"
              target="_blank"
              variant="text"
              color="primary"
            >
              <v-icon start>mdi-file-pdf-box</v-icon>
              View PDF
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-row v-else>
      <v-col cols="12" class="text-center py-12">
        <v-icon size="64" color="grey">mdi-bookmark-outline</v-icon>
        <p class="text-h6 mt-4">No saved papers yet</p>
        <p class="text-body-2 text-medium-emphasis mb-6">
          Save papers while browsing to build your reading list
        </p>
        <v-btn color="primary" :to="{ name: 'search' }">
          <v-icon start>mdi-magnify</v-icon>
          Search Papers
        </v-btn>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
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
