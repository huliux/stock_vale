<template>
  <DialogDescription
    class="text-sm text-muted-foreground"
  >
    <slot />
  </DialogDescription>
</template>

<script setup lang="ts">
import { DialogDescription } from 'radix-vue'
</script>
