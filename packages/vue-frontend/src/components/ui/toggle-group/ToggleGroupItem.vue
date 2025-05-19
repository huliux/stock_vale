<template>
  <ToggleGroupItem
    :class="cn(
      'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-accent data-[state=on]:text-accent-foreground',
      variant === 'default' &&
        'bg-transparent hover:bg-muted hover:text-muted-foreground',
      variant === 'outline' &&
        'border border-input bg-transparent hover:bg-accent hover:text-accent-foreground',
      size === 'default' && 'h-10 px-3',
      size === 'sm' && 'h-9 px-2.5',
      size === 'lg' && 'h-11 px-5',
      className
    )"
    v-bind="$attrs"
  >
    <slot />
  </ToggleGroupItem>
</template>

<script setup lang="ts">
import { ToggleGroupItem } from 'radix-vue'
import { cn } from '@/lib/utils'

defineProps<{
  variant?: 'default' | 'outline'
  size?: 'default' | 'sm' | 'lg'
  className?: string
}>()
</script>
