import { Alert, Box, Button, TextField, Typography } from "@mui/material";
import { createFileRoute, useNavigate, useRouter } from "@tanstack/react-router";
import { useState } from "react";
import { client } from "../client/client.gen";
import { getWebSocketConnections } from "../client/sdk.gen";

export const Route = createFileRoute("/auth")({
  component: Auth,
});

function Auth() {
  const { history } = useRouter();
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!inputValue.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const key = inputValue.trim();
      client.setConfig({ baseURL: import.meta.env.PROD ? "" : import.meta.env.PUBLIC_DEV_API_URL, auth: key });
      await getWebSocketConnections();
      // success
      localStorage.setItem("apiKey", key);
      history.canGoBack() ? history.back() : navigate({ to: "/" });
    } catch (e) {
      localStorage.removeItem("apiKey");
      client.setConfig({ baseURL: import.meta.env.PROD ? "" : import.meta.env.PUBLIC_DEV_API_URL, auth: undefined });
      setError("API Key 无效或网络错误，请重试。");
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "80vh",
        gap: 2,
        p: 3,
      }}
    >
      <Typography variant="h5" gutterBottom>
        请设置 API Key
      </Typography>
      <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 2, maxWidth: "400px" }}>
        需要提供有效的 API Key, 此 Key 需与 MDCx 服务器的 API_KEY 环境变量相匹配.
      </Typography>
      {error && (
        <Alert severity="error" sx={{ mb: 2, width: "100%", maxWidth: "400px" }}>
          {error}
        </Alert>
      )}
      <TextField
        label="API Key"
        variant="outlined"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        sx={{ width: "100%", maxWidth: "400px" }}
        disabled={loading}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            handleSave();
          }
        }}
      />
      <Button variant="contained" onClick={handleSave} sx={{ mt: 2 }} disabled={loading || !inputValue.trim()}>
        {loading ? "验证中..." : "保存并继续"}
      </Button>
    </Box>
  );
}
