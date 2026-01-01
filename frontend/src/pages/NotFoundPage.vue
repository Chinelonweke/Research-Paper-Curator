<template>
  <v-container class="text-center py-16">
    <v-icon size="128" color="primary" class="mb-6">mdi-file-question</v-icon>
    <h1 class="text-h2 mb-4">404</h1>
    <p class="text-h5 text-medium-emphasis mb-8">Page Not Found</p>
    <p class="text-body-1 mb-8">
      The page you're looking for doesn't exist or has been moved.
    </p>
    <v-btn color="primary" size="large" :to="{ name: 'home' }">
      <v-icon start>mdi-home</v-icon>
      Go Home
    </v-btn>
  </v-container>
</template>
