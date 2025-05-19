<template>
    <input :value="modelValue" @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)" />
</template>

<script setup lang="ts">
defineProps<{
    modelValue: any; // Temporarily widen the type
}>();

defineEmits<{
    (e: 'update:modelValue', value: any): void; // Match the prop type
}>();
</script>
