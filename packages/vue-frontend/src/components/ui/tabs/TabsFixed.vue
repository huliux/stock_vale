<script setup lang="ts">
import { Tabs as TabsPrimitive } from 'radix-vue'
import { computed, provide } from 'vue'

const props = defineProps<{
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
  activationMode?: 'automatic' | 'manual'
  dir?: 'ltr' | 'rtl'
  orientation?: 'horizontal' | 'vertical'
}>()

const emit = defineEmits<{
  'update:value': [value: string]
}>()

const modelValue = computed({
  get() {
    return props.value
  },
  set(value: string) {
    emit('update:value', value)
  },
})

provide('tabs', {
  modelValue,
})
</script>

<template>
  <TabsPrimitive
    :default-value="defaultValue"
    :model-value="modelValue"
    :activation-mode="activationMode"
    :dir="dir"
    :orientation="orientation"
    @update:model-value="
      (value) => {
        modelValue = value
        onValueChange?.(value)
      }
    "
    class="w-full"
  >
    <slot />
  </TabsPrimitive>
</template>
