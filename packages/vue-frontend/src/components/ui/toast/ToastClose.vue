<template>
  <ToastClose
    :class="cn(
      'absolute right-2 top-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100 group-[.destructive]:text-red-300 group-[.destructive]:hover:text-red-50 group-[.destructive]:focus:ring-red-400 group-[.destructive]:focus:ring-offset-red-600',
      className
    )"
    v-bind="$attrs"
  >
    <X class="h-4 w-4" />
  </ToastClose>
</template>

<script setup lang="ts">
import { ToastClose } from 'radix-vue'
import { X } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

defineProps<{
  className?: string
}>()
</script>
