<template>
  <ToastDescription
    :class="cn('text-sm opacity-90', className)"
    v-bind="$attrs"
  >
    <slot />
  </ToastDescription>
</template>

<script setup lang="ts">
import { ToastDescription } from 'radix-vue'
import { cn } from '@/lib/utils'

defineProps<{
  className?: string
}>()
</script>
