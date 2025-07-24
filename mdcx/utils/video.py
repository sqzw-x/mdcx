import json
import os
import shutil
import subprocess

try:
    import cv2

    def get_video_metadata_opencv(file_path: str) -> tuple[int, str]:
        cap = cv2.VideoCapture(file_path)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # 使用opencv获取编码器格式
        codec = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec_fourcc = (
            chr(codec & 0xFF) + chr((codec >> 8) & 0xFF) + chr((codec >> 16) & 0xFF) + chr((codec >> 24) & 0xFF)
        )
        return height, codec_fourcc

    get_video_metadata = get_video_metadata_opencv

except ImportError:
    if not shutil.which("ffprobe"):
        raise RuntimeError("当前版本无 opencv. 若想获取视频分辨率请请安装 ffprobe 或改用带 opencv 版本.")

    def get_video_metadata_ffmpeg(file_path: str) -> tuple[int, str]:
        # Use ffprobe to get video information
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", file_path]

        # macOS and Linux use default flags
        creationflags = 0
        # Windows use CREATE_NO_WINDOW to suppress the console window
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creationflags)

        data = json.loads(result.stdout)

        # Find video stream
        video_stream = next((stream for stream in data["streams"] if stream["codec_type"] == "video"), None)

        if video_stream:
            height = int(video_stream["height"])
            codec_fourcc = video_stream["codec_name"].upper()
        else:
            height = 0
            codec_fourcc = ""
        return height, codec_fourcc

    get_video_metadata = get_video_metadata_ffmpeg
