<template>
  <div class="landing-page transparent-bg">
    <ThreeBackground />
    
    <v-container class="fill-height justify-center align-center relative" style="z-index: 1">
      <v-row justify="center">
        <v-col cols="12" sm="10" md="8" lg="7">
          <v-card class="glass-panel rounded-xl pa-8 pa-md-12 text-center border-0 shadow-hero" elevation="0">
            <!-- Logo Section -->
            <div class="mb-8">
              <AppLogo size="120" class="mb-6 mx-auto" />
              <h1 class="text-h3 text-md-h2 font-weight-black text-black tracking-tighter mb-4">
                Research Paper Curator
              </h1>
              <p class="text-h6 text-medium-emphasis tracking-tight max-w-xl mx-auto">
                Unlock the future of discovery with AI-powered research curation and insights.
              </p>
            </div>

            <v-divider class="my-10 opacity-10" />

            <!-- Action Buttons -->
            <div class="d-flex flex-column flex-sm-row justify-center align-center gap-4">
              <v-btn
                :to="{ name: 'login' }"
                variant="text"
                color="black"
                size="x-large"
                class="px-10 font-weight-bold"
              >
                Sign In
              </v-btn>
              <v-btn
                :to="{ name: 'register' }"
                color="black"
                variant="flat"
                size="x-large"
                rounded="pill"
                class="px-12 font-weight-bold shadow-lg"
              >
                Get Started
                <v-icon end>mdi-arrow-right</v-icon>
              </v-btn>
            </div>

            <!-- Footer-ish info -->
            <div class="mt-12 text-caption text-medium-emphasis font-weight-medium text-uppercase tracking-widest">
              Accelerating Insight &bull; AI Curation &bull; Knowledge Hub
            </div>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import ThreeBackground from '@/components/ThreeBackground.vue'
import AppLogo from '@/components/AppLogo.vue'
</script>

<style scoped>
.landing-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  display: flex;
}

.relative {
  position: relative;
}

.max-w-xl {
  max-width: 32rem;
}

.tracking-tighter {
  letter-spacing: -0.05em !important;
}

.tracking-widest {
  letter-spacing: 0.2em !important;
}

.shadow-hero {
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15) !important;
}
</style>
