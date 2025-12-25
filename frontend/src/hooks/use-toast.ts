import * as React from "react"

type ToastVariant = "default" | "destructive"

interface Toast {
  id: string
  title?: string
  description?: string
  variant?: ToastVariant
}

interface ToastState {
  toasts: Toast[]
}

const TOAST_LIMIT = 3
const TOAST_REMOVE_DELAY = 5000

let count = 0
function genId() {
  count = (count + 1) % Number.MAX_VALUE
  return count.toString()
}

const toastState: ToastState = { toasts: [] }
const listeners: Array<(state: ToastState) => void> = []

function dispatch(action: { type: "ADD"; toast: Toast } | { type: "REMOVE"; id: string }) {
  if (action.type === "ADD") {
    toastState.toasts = [action.toast, ...toastState.toasts].slice(0, TOAST_LIMIT)
    setTimeout(() => {
      dispatch({ type: "REMOVE", id: action.toast.id })
    }, TOAST_REMOVE_DELAY)
  } else if (action.type === "REMOVE") {
    toastState.toasts = toastState.toasts.filter((t) => t.id !== action.id)
  }
  listeners.forEach((listener) => listener({ ...toastState }))
}

export function useToast() {
  const [state, setState] = React.useState<ToastState>(toastState)

  React.useEffect(() => {
    listeners.push(setState)
    return () => {
      const index = listeners.indexOf(setState)
      if (index > -1) listeners.splice(index, 1)
    }
  }, [])

  return {
    ...state,
    toast: (props: Omit<Toast, "id">) => {
      const id = genId()
      dispatch({ type: "ADD", toast: { ...props, id } })
      return id
    },
    dismiss: (id: string) => dispatch({ type: "REMOVE", id }),
  }
}
