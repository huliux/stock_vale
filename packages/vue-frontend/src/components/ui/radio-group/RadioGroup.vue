<template>
  <RadioGroupRoot
    :class="cn('grid gap-2', className)"
    v-bind="$attrs"
  >
    <slot />
  </RadioGroupRoot>
</template>

<script setup lang="ts">
import { RadioGroupRoot } from 'radix-vue'
import { cn } from '@/lib/utils'

defineProps<{
  className?: string
}>()
</script>
