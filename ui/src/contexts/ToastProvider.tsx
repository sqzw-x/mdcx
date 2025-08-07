import { Alert, Portal, Snackbar } from "@mui/material";
import type React from "react";
import { createContext, useCallback, useContext, useState } from "react";

interface Toast {
  id: string;
  message: string;
  severity: "success" | "error" | "warning" | "info";
  duration?: number;
}

type ToastContextType = {
  showToast: (message: string, severity?: "success" | "error" | "warning" | "info", duration?: number) => void;
  showSuccess: (message: string, duration?: number) => void;
  showError: (message: string, duration?: number) => void;
  showWarning: (message: string, duration?: number) => void;
  showInfo: (message: string, duration?: number) => void;
};

const ToastContext = createContext<ToastContextType | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback(
    (message: string, severity: "success" | "error" | "warning" | "info" = "info", duration = 4000) => {
      const id = Math.random().toString(36).substring(2, 9);
      const toast: Toast = {
        id,
        message,
        severity,
        duration,
      };
      setToasts((prev) => [...prev, toast]);

      // 自动移除
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    },
    [],
  );

  const showSuccess = useCallback(
    (message: string, duration?: number) => showToast(message, "success", duration),
    [showToast],
  );

  const showError = useCallback(
    (message: string, duration?: number) => showToast(message, "error", duration),
    [showToast],
  );

  const showWarning = useCallback(
    (message: string, duration?: number) => showToast(message, "warning", duration),
    [showToast],
  );

  const showInfo = useCallback(
    (message: string, duration?: number) => showToast(message, "info", duration),
    [showToast],
  );

  const handleClose = useCallback((id: string) => setToasts((prev) => prev.filter((t) => t.id !== id)), []);

  const value = { showToast, showSuccess, showError, showWarning, showInfo };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <Portal>
        {toasts.map((toast, index) => (
          <Snackbar
            key={toast.id}
            open={true}
            autoHideDuration={toast.duration}
            onClose={() => handleClose(toast.id)}
            anchorOrigin={{ vertical: "top", horizontal: "right" }}
            sx={{
              top: `${24 + index * 72}px !important`, // 增加间距以防重叠
              zIndex: 1400 + index, // 确保层级正确
            }}
          >
            <Alert
              onClose={() => handleClose(toast.id)}
              severity={toast.severity}
              variant="filled"
              sx={{
                width: "100%",
                minWidth: "300px",
                maxWidth: "500px",
                fontSize: "0.875rem",
                color: "white",
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
                borderRadius: "8px",
                "& .MuiAlert-icon": { fontSize: "1.25rem" },
                "& .MuiAlert-action": { padding: "0 4px" },
              }}
            >
              {toast.message}
            </Alert>
          </Snackbar>
        ))}
      </Portal>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
