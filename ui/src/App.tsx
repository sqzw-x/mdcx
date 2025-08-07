import "./App.css";
import CssBaseline from "@mui/material/CssBaseline";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createRouter, RouterProvider } from "@tanstack/react-router";
import { client } from "./client/client.gen";
import { ThemeProvider } from "./contexts/ThemeProvider";
import { ToastProvider } from "./contexts/ToastProvider";
import { webSocketManager } from "./hooks/useWebSocket";
import { routeTree } from "./routeTree.gen";
import { type LogEntry, useLogStore } from "./store/logStore";

const router = createRouter({ routeTree });
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// Add interceptor to handle invalid API Key
client.instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("apiKey");
      router.navigate({ to: "/auth" });
    }
    return Promise.reject(error);
  },
);

// 注册全局 WebSocket 消息处理器
webSocketManager.addHandler<LogEntry>("qt_signal", (_, msg) => {
  useLogStore.getState().addLog(msg);
});

const App = () => {
  const queryClient = new QueryClient();
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <CssBaseline />
          <RouterProvider router={router} />
          <ReactQueryDevtools />
        </ToastProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
};

export default App;
