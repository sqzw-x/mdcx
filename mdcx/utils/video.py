import json
import os
import shutil
import subprocess
from pathlib import Path

try:
    import av
except ImportError:
    av = None


def get_video_metadata_pyav(p: Path) -> tuple[int, str]:
    if av is None:
        raise ImportError("Should not be called if pyav is not available")
    height = 0
    codec_fourcc = ""
    with av.open(p) as container:
        # 查找第一个视频流
        video_stream = next((s for s in container.streams.video), None)
        if video_stream:
            height = video_stream.height
            codec_fourcc = video_stream.codec_context.name.upper()
    return height, codec_fourcc


def get_video_metadata_ffmpeg(p: Path) -> tuple[int, str]:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("当前版本无 opencv/pyav. 若想获取视频分辨率请安装 ffprobe 或改用带 opencv/pyav 版本.")
    # Use ffprobe to get video information
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(p)]

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


if av is not None:
    VIDEO_BACKEND = "pyav"
    get_video_metadata = get_video_metadata_pyav
else:
    VIDEO_BACKEND = "ffmpeg"
    get_video_metadata = get_video_metadata_ffmpeg
