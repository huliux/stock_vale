<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'
import { CalendarIcon } from 'lucide-vue-next'

const props = defineProps<{
  modelValue?: Date | string
  placeholder?: string
  class?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Date | string]
}>()

// 内部日期状态
const internalDate = ref<Date | undefined>(undefined)

// 初始化内部日期
function initInternalDate() {
  if (!props.modelValue) {
    internalDate.value = undefined
    return
  }

  if (typeof props.modelValue === 'string') {
    if (/^\d{4}-\d{2}-\d{2}$/.test(props.modelValue)) {
      const [year, month, day] = props.modelValue.split('-').map(Number)
      // JavaScript months are 0-indexed
      const date = new Date(year, month - 1, day)
      internalDate.value = isNaN(date.getTime()) ? undefined : date
    }
  } else {
    internalDate.value = props.modelValue
  }
}

// 更新模型值
function updateModelValue(date: Date | undefined) {
  if (date) {
    const formattedDate = format(date, 'yyyy-MM-dd')
    emit('update:modelValue', formattedDate)
  } else {
    emit('update:modelValue', '')
  }
}

// 处理日期选择
function handleDateSelect(date: any) {
  console.log('handleDateSelect被调用，日期:', date)
  console.log('日期类型:', typeof date)

  // 详细打印日期对象的结构
  if (date && typeof date === 'object') {
    try {
      console.log('日期对象结构:', JSON.stringify(date, null, 2))
    } catch (e) {
      console.log('日期对象无法序列化:', e)
    }
    console.log('日期属性:', Object.keys(date))

    // 检查是否是 CalendarDate
    if (date.calendar && date.year && date.month && date.day) {
      console.log('看起来是 CalendarDate 对象')
      console.log('calendar:', date.calendar)
      console.log('year:', date.year)
      console.log('month:', date.month)
      console.log('day:', date.day)

      // 创建一个 JavaScript Date 对象
      const jsDate = new Date(date.year, date.month - 1, date.day)
      console.log('转换为 JavaScript Date:', jsDate)

      // 使用 JavaScript Date 对象
      internalDate.value = jsDate
      updateModelValue(jsDate)
      return
    }

    // 检查是否是 JavaScript Date
    if (date instanceof Date) {
      console.log('是 JavaScript Date 对象')
      internalDate.value = date
      updateModelValue(date)
      return
    }
  }

  // 如果是今天的日期或者无法识别的日期类型，使用今天的日期
  if (!date) {
    console.log('日期为空，使用今天的日期')
    setToday()
  } else {
    // 尝试转换为 JavaScript Date
    try {
      const jsDate = new Date(date)
      if (!isNaN(jsDate.getTime())) {
        console.log('成功转换为 JavaScript Date:', jsDate)
        internalDate.value = jsDate
        updateModelValue(jsDate)
      } else {
        console.log('无法转换为有效的 JavaScript Date，使用今天的日期')
        setToday()
      }
    } catch (e) {
      console.log('转换日期出错，使用今天的日期:', e)
      setToday()
    }
  }
}

// 处理输入框值变化
function handleInputChange(value: string) {
  if (!value) {
    handleDateSelect(undefined)
    return
  }

  // 检查输入是否匹配YYYY-MM-DD格式
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const date = new Date(value)
    if (!isNaN(date.getTime())) {
      handleDateSelect(date)
    }
  }
}

// 设置为今天
function setToday() {
  console.log('设置为今天被调用')
  const today = new Date()
  // 强制创建一个新的日期对象，确保触发更新
  const todayFormatted = format(today, 'yyyy-MM-dd')
  const [year, month, day] = todayFormatted.split('-').map(Number)
  const newToday = new Date(year, month - 1, day)

  // 先设置内部状态
  internalDate.value = newToday
  // 然后触发更新
  updateModelValue(newToday)

  console.log('今天日期已设置为:', todayFormatted)
}

// 清除日期
function clearDate() {
  handleDateSelect(undefined)
}

// 计算输入框显示值
const inputValue = computed(() => {
  if (internalDate.value) {
    return format(internalDate.value, 'yyyy-MM-dd')
  }
  return ''
})

// 监听外部模型值变化
watch(() => props.modelValue, () => {
  initInternalDate()
}, { immediate: true })
</script>

<template>
  <Popover>
    <PopoverTrigger as-child>
      <div class="relative w-full">
        <Input :value="inputValue" @input="(e: Event) => handleInputChange((e.target as HTMLInputElement).value)"
          :placeholder="placeholder || 'YYYY-MM-DD'" :disabled="disabled" :class="cn('w-full pr-8', props.class)" />
        <Button type="button" variant="ghost" size="icon"
          class="absolute right-0 top-0 h-full px-2 text-muted-foreground" :disabled="disabled">
          <CalendarIcon class="h-4 w-4" />
        </Button>
      </div>
    </PopoverTrigger>
    <PopoverContent class="w-auto p-0" align="start">
      <Calendar :mode="'single'" v-model:selected="internalDate" @update:selected="handleDateSelect"
        class="border rounded-md" />
      <div class="p-3 border-t border-border flex justify-between">
        <Button variant="outline" size="sm" @click="setToday">今天</Button>
        <Button variant="outline" size="sm" @click="clearDate">清除</Button>
      </div>
    </PopoverContent>
  </Popover>
</template>
