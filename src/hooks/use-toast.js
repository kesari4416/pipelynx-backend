"use client";
// Inspired by react-hot-toast library
import * as React from "react"

const TOAST_LIMIT = 1
const TOAST_REMOVE_DELAY = 1000000

const actionTypes = {
  ADD_TOAST: "ADD_TOAST",
  UPDATE_TOAST: "UPDATE_TOAST",
  DISMISS_TOAST: "DISMISS_TOAST",
  REMOVE_TOAST: "REMOVE_TOAST"
}

let count = 0

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString();
}

const toastTimeouts = new Map()

const addToRemoveQueue = (toastId) => {
  if (toastTimeouts.has(toastId)) {
    return
  }

  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId)
    dispatch({
      type: "REMOVE_TOAST",
      toastId: toastId,
    })
  }, TOAST_REMOVE_DELAY)

  toastTimeouts.set(toastId, timeout)
}

// Helper: Handle ADD_TOAST action
const handleAddToast = (state, action) => ({
  ...state,
  toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
});

// Helper: Handle UPDATE_TOAST action
const handleUpdateToast = (state, action) => ({
  ...state,
  toasts: state.toasts.map((t) =>
    t.id === action.toast.id ? { ...t, ...action.toast } : t),
});

// Helper: Handle DISMISS_TOAST action
const handleDismissToast = (state, action) => {
  const { toastId } = action

  // Queue toasts for removal
  if (toastId) {
    addToRemoveQueue(toastId)
  } else {
    state.toasts.forEach((toast) => {
      addToRemoveQueue(toast.id)
    })
  }

  return {
    ...state,
    toasts: state.toasts.map((t) =>
      t.id === toastId || toastId === undefined
        ? { ...t, open: false }
        : t),
  };
}

// Helper: Handle REMOVE_TOAST action
const handleRemoveToast = (state, action) => {
  if (action.toastId === undefined) {
    return { ...state, toasts: [] }
  }
  return {
    ...state,
    toasts: state.toasts.filter((t) => t.id !== action.toastId),
  };
}

// Refactored reducer using helper functions
export const reducer = (state, action) => {
  switch (action.type) {
    case "ADD_TOAST":
      return handleAddToast(state, action);
    case "UPDATE_TOAST":
      return handleUpdateToast(state, action);
    case "DISMISS_TOAST":
      return handleDismissToast(state, action);
    case "REMOVE_TOAST":
      return handleRemoveToast(state, action);
    default:
      return state;
  }
}

const listeners = []

let memoryState = { toasts: [] }

function dispatch(action) {
  memoryState = reducer(memoryState, action)
  listeners.forEach((listener) => {
    listener(memoryState)
  })
}

function toast({
  ...props
}) {
  const id = genId()

  const update = (props) =>
    dispatch({
      type: "UPDATE_TOAST",
      toast: { ...props, id },
    })
  const dismiss = () => dispatch({ type: "DISMISS_TOAST", toastId: id })

  dispatch({
    type: "ADD_TOAST",
    toast: {
      ...props,
      id,
      open: true,
      onOpenChange: (open) => {
        if (!open) dismiss()
      },
    },
  })

  return {
    id: id,
    dismiss,
    update,
  }
}

function useToast() {
  const [state, setState] = React.useState(memoryState)

  // Subscribe to toast updates - effect runs once on mount, cleanup on unmount
  // The empty deps array is intentional: setState is stable, listeners is module-level
  React.useEffect(() => {
    const subscribe = () => {
      listeners.push(setState)
    };
    const unsubscribe = () => {
      const idx = listeners.indexOf(setState)
      if (idx > -1) {
        listeners.splice(idx, 1)
      }
    };

    subscribe();
    return unsubscribe;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return {
    ...state,
    toast,
    dismiss: (toastId) => dispatch({ type: "DISMISS_TOAST", toastId }),
  };
}

export { useToast, toast }
