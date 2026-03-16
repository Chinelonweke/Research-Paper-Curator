<template>
  <div>
    <h2 class="text-h5 mb-6 text-center font-weight-bold">Create Account</h2>

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

    <v-alert
      v-if="success"
      type="success"
      class="mb-4"
      variant="tonal"
    >
      Account created successfully! Please login.
    </v-alert>

    <v-form @submit.prevent="handleRegister" ref="formRef">
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
        v-model="username"
        label="Username"
        variant="outlined"
        density="comfortable"
        prepend-inner-icon="mdi-account"
        :rules="[rules.required, rules.username]"
        :disabled="authStore.loading"
        class="mb-4"
      />

      <v-text-field
        v-model="fullName"
        label="Full Name (optional)"
        variant="outlined"
        density="comfortable"
        prepend-inner-icon="mdi-badge-account"
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
        :rules="[rules.required, rules.minLength]"
        :disabled="authStore.loading"
        @click:append-inner="showPassword = !showPassword"
        class="mb-4"
      />

      <v-text-field
        v-model="confirmPassword"
        label="Confirm Password"
        :type="showPassword ? 'text' : 'password'"
        variant="outlined"
        density="comfortable"
        prepend-inner-icon="mdi-lock-check"
        :rules="[rules.required, rules.match]"
        :disabled="authStore.loading"
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
        Create Account
      </v-btn>
    </v-form>

    <v-divider class="my-6" />

    <p class="text-center text-body-2">
      Already have an account?
      <router-link :to="{ name: 'login' }" class="text-black text-decoration-underline font-weight-bold">
        Login here
      </router-link>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { useUIStore } from '@/stores/ui.store'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUIStore()

const formRef = ref()
const email = ref('')
const username = ref('')
const fullName = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const success = ref(false)

const rules = {
  required: (v: string) => !!v || 'This field is required',
  email: (v: string) => /.+@.+\..+/.test(v) || 'Must be a valid email',
  username: (v: string) => /^[a-zA-Z0-9_]{3,20}$/.test(v) || 'Username must be 3-20 characters (letters, numbers, underscore)',
  minLength: (v: string) => v.length >= 8 || 'Password must be at least 8 characters',
  match: (v: string) => v === password.value || 'Passwords do not match'
}

async function handleRegister() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  const result = await authStore.register({
    email: email.value,
    username: username.value,
    password: password.value,
    full_name: fullName.value || undefined
  })

  if (result) {
    success.value = true
    uiStore.showSuccess('Account created! Please login.')
    setTimeout(() => {
      router.push({ name: 'login' })
    }, 2000)
  }
}
</script>
