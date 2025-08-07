import { Wifi, WifiOff } from "@mui/icons-material";
import { Box, Chip, CircularProgress } from "@mui/material";
import { useWebSocketContext } from "@/contexts/WebSocketProvider";

export const WebSocketStatus = () => {
  const { isConnected, error } = useWebSocketContext();

  if (isConnected) {
    return <Chip icon={<Wifi />} label="已连接" color="success" variant="outlined" size="small" />;
  }

  if (error) {
    return <Chip icon={<WifiOff />} label="连接失败" color="error" variant="outlined" size="small" />;
  }

  return (
    <Chip
      icon={
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", width: 16, height: 16 }}>
          <CircularProgress size={12} thickness={4} />
        </Box>
      }
      label="连接中"
      color="warning"
      variant="outlined"
      size="small"
    />
  );
};
