<script setup lang="ts">
import NavUser from '@/components/NavUser.vue'
import DcfParametersForm from '@/components/DcfParametersForm.vue'
import StockScreenerFilters, { type ScreenerFilters } from '@/components/StockScreenerFilters.vue'
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
import { h, ref, type Component, watch } from 'vue' // ref will be needed for activeNavItem, added Component
import { useRouter, useRoute } from 'vue-router' // 导入路由器和路由
import type { ApiDcfValuationRequest } from '@shared-types/index' // Import the type

const props = withDefaults(defineProps<SidebarProps & {
  isLoading: boolean
  initialStockCode?: string | null
  dataUpdateStatus?: string
}>(), {
  collapsible: 'icon',
  dataUpdateStatus: ''
})

const emit = defineEmits<{
  (e: 'submit-valuation', payload: ApiDcfValuationRequest): void // Use specific type
  (e: 'validation-error', message: string): void
  (e: 'apply-filters', filters: Partial<ScreenerFilters>): void
  (e: 'update-data', dataType?: 'basic' | 'daily' | 'all'): void
}>()

// Dummy user data for NavUser, replace with actual data or props if needed
const dummyUser = {
  name: 'Valuation User',
  email: 'user@example.com',
  avatar: '/avatars/placeholder.jpg', // Placeholder avatar
}

// const { setOpen } = useSidebar() // Removed if not essential for sidebar functionality itself
const router = useRouter() // 获取路由器实例

interface NavItem {
  id: string
  title: string
  icon: Component // Component type for lucide icons
  path?: string // For future routing
}

const navItems: NavItem[] = [
  { id: 'valuation', title: '股票估值', icon: Calculator, path: '/' }, // 主页是估值页面
  { id: 'screener', title: '股票筛选', icon: ListFilter, path: '/screener' },
  { id: 'research', title: '深度研究', icon: FileText, path: '/deep-research' },
]

// 根据当前路由设置活动导航项
const route = useRoute()
const activeNavItemId = ref<string>('valuation') // 默认为估值

// 监听路由变化，更新活动导航项
const updateActiveNavItem = () => {
  const path = route.path
  const matchedItem = navItems.find(item => item.path === path)
  if (matchedItem) {
    activeNavItemId.value = matchedItem.id
  }
}

// 初始化时设置活动导航项
updateActiveNavItem()

// 监听路由变化
watch(() => route.path, () => {
  updateActiveNavItem()
})

const dcfFormRef = ref<InstanceType<typeof DcfParametersForm> | null>(null)
const currentStockCode = ref<string>(props.initialStockCode || '600519.SH')
const currentValuationDate = ref<string>(getTodayDateString())

// 监听initialStockCode的变化，更新currentStockCode
watch(() => props.initialStockCode, (newVal) => {
  if (newVal) {
    console.log('AppSidebar: initialStockCode变化为:', newVal);
    currentStockCode.value = newVal;
  }
}, { immediate: true })

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

// 处理筛选器事件
function handleApplyFilters(filters: Partial<ScreenerFilters>) {
  console.log('AppSidebar: handleApplyFilters被调用，filters:', filters);
  emit('apply-filters', filters);
}

function handleUpdateData(dataType: 'basic' | 'daily' | 'all' = 'all') {
  console.log('AppSidebar: handleUpdateData被调用，dataType:', dataType);
  emit('update-data', dataType);
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
                  :is-active="activeNavItemId === item.id" class="px-2.5 md:px-2" @click="() => {
                    activeNavItemId = item.id;
                    if (item.path) {
                      try {
                        // 使用replace而不是push，避免历史堆栈问题
                        router.replace(item.path);
                      } catch (error) {
                        console.error('Navigation error:', error);
                      }
                    }
                  }">
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
        <div v-else-if="activeNavItemId === 'screener'" class="h-full">
          <div class="flex flex-col h-full">
            <div class="flex-1 overflow-y-auto p-3">
              <h3 class="text-lg font-semibold mb-3">股票筛选</h3>
              <div class="max-w-full">
                <StockScreenerFilters :is-loading="props.isLoading" :data-update-status="props.dataUpdateStatus"
                  @apply-filters="handleApplyFilters" @update-data="handleUpdateData" />
              </div>
            </div>
          </div>
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
