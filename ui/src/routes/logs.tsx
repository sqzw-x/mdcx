import { Clear, VerticalAlignBottom, VerticalAlignBottomOutlined } from "@mui/icons-material";
import { Box, IconButton, Paper, Tooltip, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { WebSocketStatus } from "@/components/WebSocketStatus";
import { useLogStore } from "@/store/logStore";

export const Route = createFileRoute("/logs")({
  component: LogsComponent,
});

function LogsComponent() {
  const { logs, clearLogs } = useLogStore();
  const theme = useTheme();
  const [autoScroll, setAutoScroll] = useState(true);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && logsContainerRef.current && logs.length > 0) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [logs.length, autoScroll]);

  // 格式化时间戳
  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString("zh-CN", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      console.error("Invalid timestamp:", timestamp);
      return timestamp;
    }
  };

  return (
    <Paper
      elevation={1}
      sx={{ height: "calc(100vh - 120px)", display: "flex", flexDirection: "column", overflow: "hidden" }}
    >
      <Box
        sx={{
          p: 2,
          borderBottom: `1px solid ${theme.palette.divider}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Box>
          <Typography variant="h6">实时日志</Typography>
          <Typography variant="body2" color="text.secondary">
            共 {logs.length} 条消息
          </Typography>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <WebSocketStatus />
          <Tooltip title={autoScroll ? "禁用自动滚动" : "启用自动滚动"}>
            <IconButton
              onClick={() => setAutoScroll(!autoScroll)}
              size="small"
              color={autoScroll ? "primary" : "default"}
            >
              {autoScroll ? <VerticalAlignBottom /> : <VerticalAlignBottomOutlined />}
            </IconButton>
          </Tooltip>
          <Tooltip title="清空日志">
            <IconButton onClick={clearLogs} size="small">
              <Clear />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Box
        ref={logsContainerRef}
        sx={{
          flex: 1,
          overflow: "auto",
          fontFamily: "monospace",
          fontSize: "0.875rem",
          lineHeight: 1.4,
          backgroundColor: theme.palette.mode === "dark" ? "#1a1a1a" : "#fafafa",
        }}
      >
        {logs.map((log) => (
          <Box
            key={log.message_id}
            sx={{
              p: 1,
              borderBottom: `1px solid ${theme.palette.divider}`,
              "&:hover": { backgroundColor: theme.palette.action.hover },
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
              <Typography variant="caption" sx={{ color: theme.palette.text.secondary, minWidth: "60px" }}>
                {formatTimestamp(log.timestamp)}
              </Typography>

              <Typography
                variant="caption"
                sx={{
                  fontWeight: "bold",
                  minWidth: "80px",
                  textTransform: "uppercase",
                  color: theme.palette.mode === "dark" ? "#90caf9" : "#1976d2",
                }}
              >
                {log.data?.name}
              </Typography>
            </Box>

            <Typography
              variant="body2"
              sx={{ whiteSpace: "pre-wrap", wordBreak: "break-word", color: theme.palette.text.primary }}
            >
              {log.data?.data?.toString()}
            </Typography>
          </Box>
        ))}

        {logs.length === 0 && (
          <Box sx={{ p: 4, textAlign: "center", color: "text.secondary" }}>
            <Typography variant="body2">等待日志消息...</Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
}
