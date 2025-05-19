<template>
  <div class="container py-10 space-y-10">
    <div>
      <h1 class="text-3xl font-bold tracking-tight">组件展示</h1>
      <p class="text-muted-foreground mt-2">
        这个页面展示了项目中使用的 shadcn/ui 组件。
      </p>
    </div>

    <!-- 按钮 -->
    <section class="space-y-4">
      <h2 class="text-2xl font-semibold tracking-tight">按钮</h2>
      <div class="flex flex-wrap gap-4">
        <Button>默认按钮</Button>
        <Button variant="secondary">次要按钮</Button>
        <Button variant="destructive">危险按钮</Button>
        <Button variant="outline">轮廓按钮</Button>
        <Button variant="ghost">幽灵按钮</Button>
        <Button variant="link">链接按钮</Button>
      </div>
      <div class="flex flex-wrap gap-4">
        <Button size="sm">小按钮</Button>
        <Button>默认大小</Button>
        <Button size="lg">大按钮</Button>
        <Button size="icon" variant="outline">
          <PlusIcon class="h-4 w-4" />
        </Button>
      </div>
      <div class="flex flex-wrap gap-4">
        <Button disabled>禁用按钮</Button>
        <Button variant="outline" disabled>禁用轮廓</Button>
      </div>
    </section>

    <!-- 卡片 -->
    <section class="space-y-4">
      <h2 class="text-2xl font-semibold tracking-tight">卡片</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>卡片标题</CardTitle>
            <CardDescription>卡片描述文本</CardDescription>
          </CardHeader>
          <CardContent>
            <p>卡片内容区域</p>
          </CardContent>
          <CardFooter>
            <Button>操作按钮</Button>
          </CardFooter>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>数据卡片</CardTitle>
            <CardDescription>展示重要数据</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold">¥ 12,345.67</div>
            <p class="text-xs text-muted-foreground">相比上月增长 12%</p>
          </CardContent>
          <CardFooter>
            <Button variant="outline" size="sm">查看详情</Button>
          </CardFooter>
        </Card>
      </div>
    </section>

    <!-- 表单控件 -->
    <section class="space-y-4">
      <h2 class="text-2xl font-semibold tracking-tight">表单控件</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="space-y-4">
          <div class="space-y-2">
            <Label for="email">邮箱</Label>
            <Input id="email" placeholder="请输入邮箱地址" />
          </div>
          <div class="space-y-2">
            <Label for="password">密码</Label>
            <Input id="password" type="password" placeholder="请输入密码" />
          </div>
          <div class="flex items-center space-x-2">
            <Checkbox id="terms" />
            <Label for="terms">我同意服务条款</Label>
          </div>
          <Button>提交</Button>
        </div>
        <div class="space-y-4">
          <div class="space-y-2">
            <Label for="select">下拉选择</Label>
            <Select>
              <SelectTrigger id="select">
                <SelectValue placeholder="选择一个选项" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectLabel>水果</SelectLabel>
                  <SelectItem value="apple">苹果</SelectItem>
                  <SelectItem value="banana">香蕉</SelectItem>
                  <SelectItem value="orange">橙子</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label>单选按钮</Label>
            <div class="flex items-center space-x-2">
              <input type="radio" id="option-one" name="radio-group" value="option-one" checked />
              <Label for="option-one">选项一</Label>
            </div>
            <div class="flex items-center space-x-2">
              <input type="radio" id="option-two" name="radio-group" value="option-two" />
              <Label for="option-two">选项二</Label>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 对话框 -->
    <section class="space-y-4">
      <h2 class="text-2xl font-semibold tracking-tight">对话框</h2>
      <div>
        <Button @click="dialogOpen = true">打开对话框</Button>
        <DialogRoot :open="dialogOpen" @update:open="dialogOpen = $event">
          <DialogContent>
            <DialogHeader>
              <DialogTitle>对话框标题</DialogTitle>
              <DialogDescription>这是一个对话框示例，用于展示 shadcn/ui 的对话框组件。</DialogDescription>
            </DialogHeader>
            <div class="py-4">
              <p>对话框内容区域</p>
            </div>
            <DialogFooter>
              <Button @click="dialogOpen = false" variant="outline">取消</Button>
              <Button @click="dialogOpen = false">确认</Button>
            </DialogFooter>
          </DialogContent>
        </DialogRoot>
      </div>
    </section>

    <!-- 提醒 -->
    <section class="space-y-4">
      <h2 class="text-2xl font-semibold tracking-tight">提醒</h2>
      <div class="space-y-4">
        <Alert>
          <AlertTitle>提示</AlertTitle>
          <AlertDescription>这是一个普通提示信息。</AlertDescription>
        </Alert>
        <Alert variant="destructive">
          <AlertTitle>错误</AlertTitle>
          <AlertDescription>发生了一个错误，请稍后再试。</AlertDescription>
        </Alert>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/components/ui/select';
// import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Dialog as DialogRoot, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { PlusIcon } from 'lucide-vue-next';

const dialogOpen = ref(false);
</script>
