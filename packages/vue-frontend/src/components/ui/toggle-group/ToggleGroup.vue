<template>
  <ToggleGroupRoot :class="cn('flex items-center justify-center gap-1', className)" v-bind="$attrs">
    <slot />
  </ToggleGroupRoot>
</template>

<script setup lang="ts">
import { ToggleGroupRoot } from 'radix-vue'
import { cn } from '@/lib/utils'

defineProps<{
  className?: string
}>()
</script>
