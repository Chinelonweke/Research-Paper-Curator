<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 32 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    class="app-logo"
  >
    <!-- Background circle for depth (optional, based on theme) -->
    <rect width="32" height="32" rx="8" fill="currentColor" fill-opacity="0.05" v-if="withBackground" />
    
    <!-- Stylized Paper Stack -->
    <path
      d="M8 10C8 8.89543 8.89543 8 10 8H22C23.1046 8 24 8.89543 24 10V22C24 23.1046 23.1046 24 22 24H10C8.89543 24 8 23.1046 8 22V10Z"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linejoin="round"
    />
    <path
      d="M11 6H23C24.1046 6 25 6.89543 25 8V20"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
      opacity="0.4"
    />
    
    <!-- AI Curation/Focus Node -->
    <circle cx="16" cy="16" r="3" fill="currentColor" />
    <path
      d="M16 11V13M16 19V21M11 16H13M19 16H21"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
    />
  </svg>
</template>

<script setup lang="ts">
interface Props {
  size?: number | string
  withBackground?: boolean
}

withDefaults(defineProps<Props>(), {
  size: 32,
  withBackground: false
})
</script>

<style scoped>
.app-logo {
  display: inline-block;
  vertical-align: middle;
  transition: transform 0.3s ease;
}

.app-logo:hover {
  transform: scale(1.05);
}
</style>
