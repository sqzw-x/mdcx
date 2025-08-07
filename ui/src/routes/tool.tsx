import {
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { WebsiteSchema } from "@/client/schemas.gen";
import {
  addSubtitlesMutation,
  checkCookiesMutation,
  completeActorsMutation,
  createSymlinkMutation,
  getSiteUrlsOptions,
  scrapeSingleFileMutation,
  setSiteUrlMutation,
  startScrapeMutation,
} from "../client/@tanstack/react-query.gen";
import type { Website } from "../client/types.gen";
import { useToast } from "../contexts/ToastProvider";

export const Route = createFileRoute("/tool")({
  component: ToolComponent,
});

function ToolComponent() {
  const navigate = useNavigate();
  const { showSuccess, showError, showInfo } = useToast();

  // 开始刮削
  const startScrape = useMutation(startScrapeMutation());

  // 单文件刮削
  const [singleFilePath, setSingleFilePath] = useState("");
  const [singleFileUrl, setSingleFileUrl] = useState("");
  const scrapeSingleFile = useMutation(scrapeSingleFileMutation());

  // 创建软链接
  const [sourceDir, setSourceDir] = useState("");
  const [destDir, setDestDir] = useState("");
  const [copyFiles, setCopyFiles] = useState(false);
  const createSymlink = useMutation(createSymlinkMutation());

  // 添加字幕
  const addSubtitles = useMutation(addSubtitlesMutation());

  // 演员相关
  const completeActors = useMutation(completeActorsMutation());

  // Cookie 检查
  const checkCookies = useMutation(checkCookiesMutation());

  // 设置网站网址
  const [site, setSite] = useState<Website>("javdb");
  const [siteUrl, setSiteUrl] = useState("");
  const setSiteUrlMut = useMutation(setSiteUrlMutation());
  const currentSiteUrl = useQuery(getSiteUrlsOptions());
  const currentUrls = currentSiteUrl.isSuccess ? currentSiteUrl.data : null;
  useEffect(() => setSiteUrl(currentUrls?.[site] ?? ""), [currentUrls, site]); // 切换网站时使用当前网址

  const handleStartScrape = async () => {
    showInfo("正在启动刮削任务...");
    try {
      await startScrape.mutateAsync({});
      showSuccess("刮削任务已成功启动，正在跳转到日志页面...");
      setTimeout(() => navigate({ to: "/logs" }), 1000);
    } catch (error) {
      showError(`刮削任务启动失败: ${error}`);
    }
  };

  const handleScrapeSingleFile = async () => {
    if (!singleFilePath || !singleFileUrl) {
      showError("请输入文件路径和URL");
      return;
    }
    showInfo("正在启动单文件刮削任务...");
    try {
      await scrapeSingleFile.mutateAsync({
        body: {
          path: singleFilePath,
          url: singleFileUrl,
        },
      });
      showSuccess("单文件刮削任务已成功启动，正在跳转到日志页面...");
      setTimeout(() => navigate({ to: "/logs" }), 1000);
    } catch (error) {
      showError(`单文件刮削任务启动失败: ${error}`);
    }
  };

  const handleCreateSymlink = async () => {
    if (!sourceDir || !destDir) {
      showError("请输入源目录和目标目录");
      return;
    }
    showInfo("正在启动软链接创建任务...");
    try {
      await createSymlink.mutateAsync({
        body: {
          source_dir: sourceDir,
          dest_dir: destDir,
          copy_files: copyFiles,
        },
      });
      showSuccess("软链接创建任务已成功启动，正在跳转到日志页面...");
      setTimeout(() => navigate({ to: "/logs" }), 1000);
    } catch (error) {
      showError(`软链接创建任务启动失败: ${error}`);
    }
  };

  const handleAddSubtitles = async () => {
    showInfo("正在启动字幕检查和添加任务...");
    try {
      await addSubtitles.mutateAsync({});
      showSuccess("字幕检查和添加任务已成功启动，正在跳转到日志页面...");
      setTimeout(() => navigate({ to: "/logs" }), 1000);
    } catch (error) {
      showError(`字幕添加任务启动失败: ${error}`);
    }
  };

  const handleCompleteActors = async () => {
    showInfo("正在启动演员信息补全任务...");
    try {
      await completeActors.mutateAsync({});
      showSuccess("演员信息补全任务已成功启动，正在跳转到日志页面...");
      setTimeout(() => navigate({ to: "/logs" }), 1000);
    } catch (error) {
      showError(`演员信息补全任务启动失败: ${error}`);
    }
  };

  const handleCheckCookies = async () => {
    showInfo("正在检查Cookie有效性...");
    try {
      await checkCookies.mutateAsync({});
      showSuccess("Cookie检查已完成。");
    } catch (error) {
      showError(`Cookie检查失败: ${error}`);
    }
  };

  const handleSetSiteUrl = async () => {
    try {
      await setSiteUrlMut.mutateAsync({ body: { site, url: siteUrl } });
      await currentSiteUrl.refetch(); // 重新获取服务器设置
      siteUrl ? showSuccess(`成功设置 ${site} 网址: ${siteUrl}`) : showSuccess(`已清除 ${site} 的自定义网址`);
    } catch (error) {
      showError(`设置网站网址失败: ${error}`);
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        工具集合
      </Typography>

      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
        {/* 刮削工具 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              刮削工具
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <Button
                variant="contained"
                onClick={handleStartScrape}
                disabled={startScrape.isPending}
                sx={{ alignSelf: "flex-start" }}
              >
                {startScrape.isPending ? "正在启动..." : "开始刮削"}
              </Button>

              <Typography variant="subtitle1">单文件刮削</Typography>
              <Box
                sx={{
                  display: "flex",
                  gap: 2,
                  alignItems: "flex-end",
                  flexWrap: "wrap",
                }}
              >
                <TextField
                  label="文件路径"
                  value={singleFilePath}
                  onChange={(e) => setSingleFilePath(e.target.value)}
                  size="small"
                  sx={{ flexGrow: 1, minWidth: 200 }}
                />
                <TextField
                  label="URL"
                  value={singleFileUrl}
                  onChange={(e) => setSingleFileUrl(e.target.value)}
                  size="small"
                  sx={{ flexGrow: 1, minWidth: 200 }}
                />
                <Button
                  variant="outlined"
                  onClick={handleScrapeSingleFile}
                  disabled={scrapeSingleFile.isPending}
                  sx={{ whiteSpace: "nowrap" }}
                >
                  {scrapeSingleFile.isPending ? "正在刮削..." : "单文件刮削"}
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* 文件管理工具和演员工具 */}
        <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
          <Card sx={{ flex: "1 1 400px" }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                文件管理工具
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <Typography variant="subtitle1">创建软链接</Typography>
                <TextField
                  label="源目录"
                  value={sourceDir}
                  onChange={(e) => setSourceDir(e.target.value)}
                  size="small"
                  fullWidth
                />
                <TextField
                  label="目标目录"
                  value={destDir}
                  onChange={(e) => setDestDir(e.target.value)}
                  size="small"
                  fullWidth
                />
                <FormControlLabel
                  control={<Checkbox checked={copyFiles} onChange={(e) => setCopyFiles(e.target.checked)} />}
                  label="复制 nfo, 图片, 字幕等文件"
                />
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                  <Button
                    variant="outlined"
                    onClick={handleCreateSymlink}
                    disabled={createSymlink.isPending}
                    size="small"
                  >
                    {createSymlink.isPending ? "正在创建..." : "创建软链接"}
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={handleAddSubtitles}
                    disabled={addSubtitles.isPending}
                    size="small"
                  >
                    {addSubtitles.isPending ? "正在处理..." : "检查并添加字幕"}
                  </Button>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ flex: "1 1 300px" }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                演员工具
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <Button
                  variant="outlined"
                  onClick={handleCompleteActors}
                  disabled={completeActors.isPending}
                  sx={{ alignSelf: "flex-start" }}
                >
                  {completeActors.isPending ? "正在补全..." : "补全演员信息"}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* 网站设置工具 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              网站设置工具
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <Button
                variant="outlined"
                onClick={handleCheckCookies}
                disabled={checkCookies.isPending}
                sx={{ alignSelf: "flex-start" }}
              >
                {checkCookies.isPending ? "正在检查..." : "Cookie 有效性检查"}
              </Button>

              <Typography variant="subtitle1">设置网站自定义网址</Typography>
              <Box
                sx={{
                  display: "flex",
                  gap: 2,
                  alignItems: "flex-end",
                  flexWrap: "wrap",
                }}
              >
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>网站</InputLabel>
                  <Select value={site} label="网站" onChange={(e) => setSite(e.target.value)}>
                    {WebsiteSchema.enum.map((w) => (
                      <MenuItem key={w} value={w}>
                        {w}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <TextField
                  label="自定义URL"
                  value={siteUrl}
                  onChange={(e) => setSiteUrl(e.target.value)}
                  size="small"
                  sx={{ flexGrow: 1, minWidth: 200 }}
                />
                <Button
                  variant="outlined"
                  onClick={handleSetSiteUrl}
                  disabled={setSiteUrlMut.isPending}
                  sx={{ whiteSpace: "nowrap" }}
                >
                  {setSiteUrlMut.isPending ? "正在设置..." : "设置网站网址"}
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}
