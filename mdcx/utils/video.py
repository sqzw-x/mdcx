import json
import os
import shutil
import subprocess

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import av
except ImportError:
    av = None


def get_video_metadata_opencv(file_path: str) -> tuple[int, str]:
    if cv2 is None:
        raise ImportError("Should not be called if opencv is not available")
    cap = cv2.VideoCapture(file_path)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # 使用opencv获取编码器格式
    codec = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec_fourcc = chr(codec & 0xFF) + chr((codec >> 8) & 0xFF) + chr((codec >> 16) & 0xFF) + chr((codec >> 24) & 0xFF)
    return height, codec_fourcc.upper()


def get_video_metadata_pyav(file_path: str) -> tuple[int, str]:
    if av is None:
        raise ImportError("Should not be called if pyav is not available")
    height = 0
    codec_fourcc = ""
    with av.open(file_path) as container:
        # 查找第一个视频流
        video_stream = next((s for s in container.streams.video), None)
        if video_stream:
            height = video_stream.height
            codec_fourcc = video_stream.codec_context.name.upper()
    return height, codec_fourcc


def get_video_metadata_ffmpeg(file_path: str) -> tuple[int, str]:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("当前版本无 opencv/pyav. 若想获取视频分辨率请安装 ffprobe 或改用带 opencv/pyav 版本.")
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


if cv2 is not None:
    print("Using OpenCV for video metadata extraction")
    get_video_metadata = get_video_metadata_opencv
elif av is not None:
    print("Using PyAV for video metadata extraction")
    get_video_metadata = get_video_metadata_pyav
else:
    print("Using FFmpeg for video metadata extraction")
    get_video_metadata = get_video_metadata_ffmpeg
