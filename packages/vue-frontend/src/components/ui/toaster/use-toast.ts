import { ref, computed } from 'vue'

export type ToastProps = {
  id: string
  title?: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  variant?: 'default' | 'destructive' | 'success'
  class?: string
}

const TOAST_LIMIT = 5
const TOAST_REMOVE_DELAY = 5000

const actionTypes = {
  ADD_TOAST: 'ADD_TOAST',
  UPDATE_TOAST: 'UPDATE_TOAST',
  DISMISS_TOAST: 'DISMISS_TOAST',
  REMOVE_TOAST: 'REMOVE_TOAST'
} as const

let count = 0

function generateId() {
  count = (count + 1) % Number.MAX_VALUE
  return count.toString()
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

const toasts = ref<ToastProps[]>([])

const addToast = (toast: Omit<ToastProps, 'id'>) => {
  const id = generateId()

  const newToast = {
    ...toast,
    id
  }

  toasts.value = [newToast, ...toasts.value].slice(0, TOAST_LIMIT)

  const timeout = setTimeout(() => {
    dismissToast(id)
  }, TOAST_REMOVE_DELAY)

  toastTimeouts.set(id, timeout)

  return id
}

const dismissToast = (id: string) => {
  toasts.value = toasts.value.filter((t) => t.id !== id)

  if (toastTimeouts.has(id)) {
    clearTimeout(toastTimeouts.get(id))
    toastTimeouts.delete(id)
  }
}

export const useToast = () => {
  return {
    toasts: computed(() => toasts.value),
    toast: (props: Omit<ToastProps, 'id'>) => addToast(props),
    dismiss: (id: string) => dismissToast(id),
    error: (props: Omit<ToastProps, 'id' | 'variant'>) => addToast({ ...props, variant: 'destructive' }),
    success: (props: Omit<ToastProps, 'id' | 'variant'>) => addToast({ ...props, variant: 'success' })
  }
}
