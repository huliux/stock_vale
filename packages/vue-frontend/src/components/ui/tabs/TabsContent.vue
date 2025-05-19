<script setup lang="ts">
import { TabsContent as TabsContentPrimitive } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  value: string
  forceMount?: boolean
  class?: string
}>()
</script>

<template>
  <TabsContentPrimitive
    :value="value"
    :force-mount="forceMount"
    :class="cn(
      'mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
      props.class
    )"
  >
    <slot />
  </TabsContentPrimitive>
</template>
