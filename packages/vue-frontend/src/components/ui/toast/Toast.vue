<template>
  <ToastProvider>
    <slot />
  </ToastProvider>
</template>

<script setup lang="ts">
import { ToastProvider } from 'radix-vue'
</script>
