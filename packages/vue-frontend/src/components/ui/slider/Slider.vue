<script setup lang="ts">
import { SliderRoot as SliderPrimitive, SliderTrack, SliderRange, SliderThumb } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  modelValue?: number | number[]
  defaultValue?: number | number[]
  min?: number
  max?: number
  step?: number
  orientation?: 'horizontal' | 'vertical'
  disabled?: boolean
  inverted?: boolean
  class?: string
  name?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | number[]]
}>()
</script>

<template>
  <SliderPrimitive :model-value="modelValue" :default-value="defaultValue" :min="min" :max="max" :step="step"
    :orientation="orientation" :disabled="disabled" :inverted="inverted" :name="name"
    @update:model-value="emit('update:modelValue', $event)"
    :class="cn('relative flex w-full touch-none select-none items-center', props.class)">
    <SliderTrack class="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
      <SliderRange class="absolute h-full bg-primary" />
    </SliderTrack>
    <SliderThumb v-for="(_, index) in Array.isArray(modelValue || defaultValue)
      ? modelValue || defaultValue
      : [modelValue || defaultValue]" :key="index"
      class="block h-5 w-5 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50" />
  </SliderPrimitive>
</template>
