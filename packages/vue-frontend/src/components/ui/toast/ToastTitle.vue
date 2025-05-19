<template>
  <ToastTitle
    :class="cn('text-sm font-semibold', className)"
    v-bind="$attrs"
  >
    <slot />
  </ToastTitle>
</template>

<script setup lang="ts">
import { ToastTitle } from 'radix-vue'
import { cn } from '@/lib/utils'

defineProps<{
  className?: string
}>()
</script>
