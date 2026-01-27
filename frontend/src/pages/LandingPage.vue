<template>
  <div class="landing-hero">
    <div class="landing-card glass-panel">
      <v-icon size="72" color="black">mdi-book-open-page-variant</v-icon>
      <h1 class="text-h2 font-weight-bold mt-4">Research Paper Curator</h1>
      <p class="text-h6 text-medium-emphasis mb-6">Unlock AI-powered research insights</p>

      <div class="d-flex justify-center gap-4">
        <v-btn :to="{ name: 'login' }" color="black" variant="text">Login</v-btn>
        <v-btn :to="{ name: 'register' }" color="black" variant="outlined">Register</v-btn>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Simple landing page used for unauthenticated access
</script>

<style scoped>
.landing-hero {
  background-color: #808080;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem 1rem;
}
.landing-card {
  max-width: 820px;
  width: 100%;
  padding: 2.5rem;
  border-radius: 10px;
  text-align: center;
}
</style>
