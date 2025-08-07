import { createContext, useContext } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";

const WebSocketContext = createContext<ReturnType<typeof useWebSocket> | null>(null);

export const WebSocketProvider = ({ children }: { children: React.ReactNode }) => {
  const wsHost = import.meta.env.PROD ? "" : import.meta.env.PUBLIC_DEV_WS_URL;
  const wsURL = `${wsHost}/api/v1/ws/`;
  const ws = useWebSocket(wsURL);
  return <WebSocketContext.Provider value={ws}>{children}</WebSocketContext.Provider>;
};

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocketContext must be used within a WebSocketProvider");
  }
  return context;
};
