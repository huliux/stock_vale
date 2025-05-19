<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-4">测试页面</h1>
    <p class="mb-4">这是一个简单的测试页面，用于验证基本功能是否正常。</p>
    
    <div class="p-4 bg-white rounded-md shadow mb-4">
      <h2 class="text-lg font-semibold mb-2">基本组件测试</h2>
      <Button @click="count++">点击了 {{ count }} 次</Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Button } from '@/components/ui/button';

const count = ref(0);
</script>
