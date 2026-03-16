<template>
  <div>
    <h2 class="text-h5 mb-6 text-center font-weight-bold">Welcome Back</h2>

    <v-alert
      v-if="authStore.error"
      type="error"
      class="mb-4"
      closable
      variant="tonal"
      @click:close="authStore.clearError"
    >
      {{ authStore.error }}
    </v-alert>

    <v-form @submit.prevent="handleLogin" ref="formRef">
      <v-text-field
        v-model="email"
        label="Email"
        type="email"
        variant="outlined"
        density="comfortable"
        prepend-inner-icon="mdi-email"
        :rules="[rules.required, rules.email]"
        :disabled="authStore.loading"
        class="mb-4"
      />

      <v-text-field
        v-model="password"
        label="Password"
        :type="showPassword ? 'text' : 'password'"
        variant="outlined"
        density="comfortable"
        prepend-inner-icon="mdi-lock"
        :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
        :rules="[rules.required]"
        :disabled="authStore.loading"
        @click:append-inner="showPassword = !showPassword"
        class="mb-6"
      />

      <v-btn
        type="submit"
        color="black"
        variant="flat"
        elevation="0"
        size="large"
        block
        :loading="authStore.loading"
      >
        Login
      </v-btn>
    </v-form>

    <v-divider class="my-6" />

    <p class="text-center text-body-2">
      Don't have an account?
      <router-link :to="{ name: 'register' }" class="text-black text-decoration-underline font-weight-bold">
        Register here
      </router-link>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { useUIStore } from '@/stores/ui.store'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const uiStore = useUIStore()

const formRef = ref()
const email = ref('')
const password = ref('')
const showPassword = ref(false)

const rules = {
  required: (v: string) => !!v || 'This field is required',
  email: (v: string) => /.+@.+\..+/.test(v) || 'Must be a valid email'
}

async function handleLogin() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  const success = await authStore.login({
    email: email.value,
    password: password.value
  })

  if (success) {
    uiStore.showSuccess('Welcome back!')
    const redirect = route.query.redirect as string
    router.push(redirect || '/')
  }
}
</script>
