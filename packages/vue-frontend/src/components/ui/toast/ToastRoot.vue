<template>
  <ToastRoot
    :class="cn(
      'group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full',
      variantStyles[variant()],
      className
    )"
    v-bind="$attrs"
  >
    <slot />
  </ToastRoot>
</template>

<script setup lang="ts">
import { ToastRoot } from 'radix-vue'
import { cn } from '@/lib/utils'
import { computed } from 'vue'

const props = defineProps<{
  variant?: 'default' | 'destructive' | 'success'
  className?: string
}>()

const variant = computed(() => props.variant || 'default')

const variantStyles = {
  default: 'bg-background border',
  destructive:
    'destructive group border-destructive bg-destructive text-destructive-foreground',
  success:
    'success group border-success bg-success text-success-foreground',
}
</script>
