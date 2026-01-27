<template>
  <div class="landing-hero">
    <div class="pen-bg">
      <span class="pen" style="left:8%; top:18%; --rot:-20deg; --dur:9s; animation-delay:0s"></span>
      <span class="pen" style="left:25%; top:8%; --rot:10deg; --dur:7.5s; animation-delay:-2s"></span>
      <span class="pen" style="left:45%; top:22%; --rot:-10deg; --dur:8.5s; animation-delay:-1s"></span>
      <span class="pen" style="left:62%; top:12%; --rot:15deg; --dur:10s; animation-delay:-3s"></span>
      <span class="pen" style="left:78%; top:25%; --rot:-5deg; --dur:9.5s; animation-delay:-1.5s"></span>
    </div>

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
  position: relative;
  overflow: hidden;
}

.pen-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.pen {
  position: absolute;
  width: 140px;
  height: 32px;
  background-repeat: no-repeat;
  background-size: contain;
  opacity: 0.12;
  transform-origin: center;
  /* simple pen-shaped SVG as background */
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 16'><rect x='0' y='4' width='48' height='8' rx='2' fill='%23000'/><rect x='48' y='0' width='12' height='16' rx='2' fill='%23333'/></svg>");
  animation: float var(--dur,8s) linear infinite;
}

@keyframes float {
  0% { transform: translateY(0) rotate(var(--rot,0deg)); opacity: 0.06; }
  25% { transform: translateY(-18px) rotate(calc(var(--rot, 0deg) + 4deg)); opacity: 0.12; }
  50% { transform: translateY(-36px) rotate(calc(var(--rot, 0deg) - 6deg)); opacity: 0.16; }
  75% { transform: translateY(-18px) rotate(calc(var(--rot, 0deg) + 2deg)); opacity: 0.12; }
  100% { transform: translateY(0) rotate(var(--rot,0deg)); opacity: 0.06; }
}

.landing-card {
  max-width: 820px;
  width: 100%;
  padding: 2.5rem;
  border-radius: 10px;
  text-align: center;
  z-index: 1;
  /* make sure text inside is black */
  color: black !important;
}

.landing-card, .landing-card * {
  color: black !important;
}

.landing-card .text-medium-emphasis {
  color: #444444 !important;
}
</style>
