import { useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";

export type MessageType =
  | "ping"
  | "pong"
  | "connect"
  | "disconnect"
  | "notification"
  | "error"
  | "progress"
  | "status"
  | "qt_signal"
  | "custom";

export interface WebSocketMessage<T = unknown> {
  type: MessageType;
  data: T | null;
  timestamp: string;
  message_id: string;
  client_id?: string;
}

type MessageHandler<T = unknown> = (data: T, msg: WebSocketMessage<T>) => void;

class WebSocketManager {
  private static instance: WebSocketManager;

  private ws: WebSocket | null = null;
  private url: string = "";
  private reconnectTimeoutId: NodeJS.Timeout | null = null;
  private isConnecting: boolean = false;

  private connectionState: boolean = false;
  private errorState: string | null = null;

  // biome-ignore lint/suspicious/noExplicitAny: 允许任何类型的 MessageHandler
  private handlers: Map<string, Set<MessageHandler<any>>> = new Map();
  private stateListeners: Set<() => void> = new Set();

  private constructor() {}

  public static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  public connect(url: string, navigate: ReturnType<typeof useNavigate>) {
    if (this.ws || this.isConnecting) return;
    this.url = url;
    this.isConnecting = true;
    console.log("WebSocketManager: Attempting to connect...");

    const apiKey = localStorage.getItem("apiKey");
    if (!apiKey) {
      console.warn("WebSocketManager: No API key found. Redirecting to auth.");
      this.isConnecting = false;
      navigate({ to: "/auth" });
      return;
    }

    const b64Key = btoa(apiKey).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
    this.ws = new WebSocket(this.url, ["v1.mdcx", `base64.ws.key.${b64Key}`]);

    this.ws.onopen = this.handleOpen.bind(this);
    this.ws.onmessage = this.handleMessage.bind(this);
    this.ws.onclose = this.handleClose.bind(this, navigate);
    this.ws.onerror = this.handleError.bind(this);
  }

  public disconnect() {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }
    if (this.ws) {
      this.ws.onclose = null; // Prevent reconnect on manual close
      this.ws.close();
      this.ws = null;
    }
    this.isConnecting = false;
    console.log("WebSocketManager: Manually disconnected.");
  }

  public sendMessage(message: unknown) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error("WebSocket is not connected.");
    }
  }

  /**
   * 为特定消息类型添加处理器
   * @param messageType 消息类型
   * @param handler 处理器函数
   * @returns 取消订阅的函数
   */
  public addHandler<T>(messageType: MessageType, handler: MessageHandler<T>): () => void {
    if (!this.handlers.has(messageType)) {
      this.handlers.set(messageType, new Set());
    }
    const handlers = this.handlers.get(messageType);
    if (handlers) {
      handlers.add(handler);
      return () => {
        handlers.delete(handler);
        if (handlers.size === 0) this.handlers.delete(messageType);
      };
    }
    return () => {};
  }
  public addStateListener(listener: () => void): () => void {
    this.stateListeners.add(listener);
    return () => this.stateListeners.delete(listener);
  }
  public getState() {
    return { isConnected: this.connectionState, error: this.errorState };
  }

  private handleOpen() {
    console.log("WebSocket connected");
    this.isConnecting = false;
    this.connectionState = true;
    this.errorState = null;
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }
    this.notifyStateChange();
  }

  private handleMessage(event: MessageEvent) {
    if (typeof event.data !== "string") {
      console.error("binary data is not supported");
      return;
    }

    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      const handlers = this.handlers.get(message.type);
      if (handlers) {
        handlers.forEach((handler) => handler(message.data, message));
      } else {
        console.warn(`No handlers registered for message type: ${message.type}`);
        console.debug("Received message:", message);
      }
    } catch (error) {
      console.error("Failed to parse WebSocket message:", error);
    }
  }

  private handleClose(navigate: ReturnType<typeof useNavigate>, event: CloseEvent) {
    console.log("WebSocket disconnected:", event.reason);
    this.ws = null;
    this.isConnecting = false;
    this.connectionState = false;
    this.errorState = event.reason || "WebSocket closed unexpectedly";
    this.notifyStateChange();

    // Reconnect logic
    if (!this.reconnectTimeoutId && import.meta.env.PUBLIC_DEV_ENABLE_WS === "true") {
      console.log("WebSocketManager: Scheduling reconnect in 5s...");
      this.reconnectTimeoutId = setTimeout(() => {
        this.reconnectTimeoutId = null;
        this.connect(this.url, navigate);
      }, 5000);
    }
  }

  private handleError(event: Event) {
    console.error("WebSocket error:", event);
    this.errorState = "WebSocket error occurred.";
    this.notifyStateChange();
    this.ws?.close();
  }

  private notifyStateChange() {
    this.stateListeners.forEach((listener) => listener());
  }
}

export const webSocketManager = WebSocketManager.getInstance();

/**
 * useWebSocket Hook
 *
 * This hook provides an interface to the global WebSocketManager singleton.
 * It allows components to subscribe to WebSocket state and messages.
 */
export const useWebSocket = (url: string) => {
  const navigate = useNavigate();
  const [state, setState] = useState(webSocketManager.getState());
  const managerRef = useRef(webSocketManager);

  useEffect(() => {
    // Function to update state from manager
    const handleStateChange = () => {
      setState(webSocketManager.getState());
    };
    // Connect on mount if not already connected
    managerRef.current.connect(url, navigate);
    // Subscribe to state changes
    const unsubscribe = managerRef.current.addStateListener(handleStateChange);
    // On component unmount, clean up the listener
    return () => unsubscribe();
  }, [url, navigate]);

  const sendMessage = useCallback((data: unknown) => {
    managerRef.current.sendMessage(data);
  }, []);

  const addHandler = useCallback(
    <T>(messageType: MessageType, handler: MessageHandler<T>) => managerRef.current.addHandler(messageType, handler),
    [],
  );

  return { isConnected: state.isConnected, error: state.error, sendMessage, addHandler };
};
