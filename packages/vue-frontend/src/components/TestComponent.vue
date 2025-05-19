<template>
  <div class="p-4 border rounded-md">
    <h2 class="text-lg font-semibold mb-4">测试组件</h2>
    <p>这是一个简单的测试组件，用于验证基本功能是否正常。</p>
    <Button class="mt-4" @click="count++">点击了 {{ count }} 次</Button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'

const count = ref(0)
</script>
