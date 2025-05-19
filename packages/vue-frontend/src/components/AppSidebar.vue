<script setup lang="ts">
import NavUser from '@/components/NavUser.vue'
import DcfParametersForm from '@/components/DcfParametersForm.vue'
import QuickValuationCard from '@/components/QuickValuationCard.vue'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  // SidebarInput, // Removed example-specific import
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  type SidebarProps,
  useSidebar, // Added back to get isOpen state
} from '@/components/ui/sidebar'
// import { Label } from '@/components/ui/label' // Removed example-specific import
// import { Switch } from '@/components/ui/switch' // Removed example-specific import
import { Command, Calculator, ListFilter, FileText } from 'lucide-vue-next' // Updated icons
import { h, ref, type Component } from 'vue' // ref will be needed for activeNavItem, added Component
import type { ApiDcfValuationRequest } from '@shared-types/index' // Import the type

const props = withDefaults(defineProps<SidebarProps & {
  isLoading: boolean
  initialStockCode?: string | null
}>(), {
  collapsible: 'icon',
})

const emit = defineEmits<{
  (e: 'submit-valuation', payload: ApiDcfValuationRequest): void // Use specific type
  (e: 'validation-error', message: string): void
}>()

// Dummy user data for NavUser, replace with actual data or props if needed
const dummyUser = {
  name: 'Valuation User',
  email: 'user@example.com',
  avatar: '/avatars/placeholder.jpg', // Placeholder avatar
}

// const { setOpen } = useSidebar() // Removed if not essential for sidebar functionality itself

interface NavItem {
  id: string
  title: string
  icon: Component // Component type for lucide icons
  path?: string // For future routing
}

const navItems: NavItem[] = [
  { id: 'valuation', title: '股票估值', icon: Calculator, path: '/valuation' },
  { id: 'screener', title: '股票筛选', icon: ListFilter, path: '/screener' },
  { id: 'research', title: '深度研究', icon: FileText, path: '/research' },
]

const activeNavItemId = ref<string>(navItems[0].id) // Default to first item
const dcfFormRef = ref<InstanceType<typeof DcfParametersForm> | null>(null)
const currentStockCode = ref<string>(props.initialStockCode || '600519.SH')
const currentValuationDate = ref<string>(getTodayDateString())

const { open } = useSidebar() // Get the open state from the provider, changed isOpen to open

function getTodayDateString() {
  // 强制创建一个新的日期对象，确保获取当前日期
  const today = new Date();
  const year = today.getFullYear();
  const month = (today.getMonth() + 1).toString().padStart(2, '0');
  const day = today.getDate().toString().padStart(2, '0');
  const todayString = `${year}-${month}-${day}`;
  console.log('AppSidebar: 获取今天日期:', todayString);
  return todayString;
}

function handleQuickSubmit(stockCode: string, valuationDate: string) {
  console.log('AppSidebar: handleQuickSubmit被调用，stockCode:', stockCode, 'valuationDate:', valuationDate);

  // 检查是否是今天的日期
  const todayString = getTodayDateString();

  // 设置股票代码
  currentStockCode.value = stockCode;

  // 设置日期，如果是今天的日期，使用getTodayDateString()确保正确处理
  if (valuationDate === todayString) {
    console.log('AppSidebar: 使用今天日期');
    currentValuationDate.value = todayString;
  } else {
    console.log('AppSidebar: 使用指定日期:', valuationDate);
    currentValuationDate.value = valuationDate;
  }

  // 触发表单提交
  if (dcfFormRef.value) {
    console.log('AppSidebar: 调用dcfFormRef.submitValuationRequest()');
    dcfFormRef.value.submitValuationRequest()
  } else {
    console.error('AppSidebar: dcfFormRef为null，无法提交表单');
  }
}

</script>

<template>
  <Sidebar class="overflow-hidden *:data-[sidebar=sidebar]:flex-row" v-bind="props">
    <!-- This is the first sidebar (Icon Bar) -->
    <Sidebar collapsible="none" class="w-[calc(var(--sidebar-width-icon)+1px)]! border-r">
      <SidebarHeader class="h-14 flex items-center justify-center border-b">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" as-child class="md:h-8 md:p-0">
              <a href="#" @click.prevent="activeNavItemId = 'dashboard'"> <!-- Or some default/home icon action -->
                <div
                  class="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  <Command class="size-4" />
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent class="px-1.5 md:px-0">
            <SidebarMenu>
              <SidebarMenuItem v-for="item in navItems" :key="item.id">
                <SidebarMenuButton :tooltip="h('div', { hidden: false }, item.title)"
                  :is-active="activeNavItemId === item.id" class="px-2.5 md:px-2"
                  @click="() => activeNavItemId = item.id">
                  <component :is="item.icon" class="size-4" />
                  <span v-show="open">{{ item.title }}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <NavUser :user="dummyUser" />
      </SidebarFooter>
    </Sidebar>

    <!--  This is the second sidebar (Content Panel) -->
    <Sidebar collapsible="none" class="hidden flex-1 md:flex bg-muted/20">
      <SidebarHeader v-if="navItems.find(item => item.id === activeNavItemId)"
        class="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background p-4">
        <h3 class="text-lg font-semibold text-foreground">{{navItems.find(item => item.id === activeNavItemId)?.title}}
        </h3>
      </SidebarHeader>
      <SidebarContent class="p-2 bg-muted/50">
        <div v-if="activeNavItemId === 'valuation'" class="h-full">
          <div class="flex flex-col h-full">
            <div class="flex-1 overflow-y-auto">
              <DcfParametersForm ref="dcfFormRef" :is-loading="props.isLoading" :stock-code="currentStockCode"
                :valuation-date="currentValuationDate" @submit-valuation="payload => {
                  console.log('AppSidebar: 接收到submit-valuation事件，转发到父组件');
                  emit('submit-valuation', payload);
                }" @validation-error="message => {
                  console.log('AppSidebar: 接收到validation-error事件，转发到父组件');
                  emit('validation-error', message);
                }" />
            </div>
            <div class="mt-auto">
              <QuickValuationCard :is-loading="props.isLoading" :initial-stock-code="props.initialStockCode"
                @submit="(stockCode, valuationDate) => handleQuickSubmit(stockCode, valuationDate)" />
            </div>
          </div>
        </div>
        <div v-else-if="activeNavItemId === 'screener'" class="p-4">
          <p>股票筛选参数区 (待实现)</p>
        </div>
        <div v-else-if="activeNavItemId === 'research'" class="p-4">
          <p>深度研究参数区 (待实现)</p>
        </div>
        <div v-else class="p-4">
          <p>请选择一个导航项</p>
        </div>
      </SidebarContent>
    </Sidebar>
  </Sidebar>
</template>
