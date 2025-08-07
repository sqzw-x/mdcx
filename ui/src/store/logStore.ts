import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import type { WebSocketMessage } from "@/hooks/useWebSocket";

// 日志条目接口, 对应服务器上 qt signal message
export interface LogEntry {
  name: string;
  data: string | object | null;
}

interface LogStore {
  logs: WebSocketMessage<LogEntry>[];

  // Actions
  addLog: (log: WebSocketMessage<LogEntry>) => void;
  clearLogs: () => void;
}

export const useLogStore = create<LogStore>()(
  subscribeWithSelector((set) => ({
    logs: [],

    addLog: (log) =>
      set((state) => {
        const newLogs = [...state.logs, log];
        // 保持最多 1000 条日志以防止内存溢出
        if (newLogs.length > 1000) {
          return { logs: newLogs.slice(-1000) };
        }
        return { logs: newLogs };
      }),

    clearLogs: () => set({ logs: [] }),
  })),
);
