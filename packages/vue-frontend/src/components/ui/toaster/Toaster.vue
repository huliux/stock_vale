<template>
  <Toast>
    <ToastViewport />
    <ToastRoot
      v-for="toast in toasts"
      :key="toast.id"
      :variant="toast.variant"
      :class="toast.class"
    >
      <div class="grid gap-1">
        <ToastTitle v-if="toast.title">{{ toast.title }}</ToastTitle>
        <ToastDescription v-if="toast.description">
          {{ toast.description }}
        </ToastDescription>
      </div>
      <ToastClose />
    </ToastRoot>
  </Toast>
</template>

<script setup lang="ts">
import { useToast } from '@/components/ui/toaster/use-toast'
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastRoot,
  ToastTitle,
  ToastViewport,
} from '@/components/ui/toast'

const { toasts } = useToast()
</script>
