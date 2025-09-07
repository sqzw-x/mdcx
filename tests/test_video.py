import os
import subprocess

import pytest

from mdcx.utils.video import get_video_metadata_ffmpeg, get_video_metadata_pyav


def create_dummy_video(path, size="320x240", vcodec="libx264", fmt="mp4", pix_fmt=None):
    # 支持不同分辨率、编码、格式
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc=duration=1:size={size}:rate=1"]
    if pix_fmt:
        cmd += ["-pix_fmt", pix_fmt]
    cmd += ["-c:v", vcodec, path]
    subprocess.run(cmd, check=True)


VIDEO_CASES = [
    ("test_h264_240p.mp4", "320x240", "libx264", "mp4", None, 240, "H264"),
    ("test_h264_720p.mp4", "1280x720", "libx264", "mp4", None, 720, "H264"),
    ("test_mpeg4_360p.avi", "640x360", "mpeg4", "avi", None, 360, "MPEG4"),
    ("test_h265_480p.mkv", "854x480", "libx265", "mkv", None, 480, "HEVC"),
    ("test_vp8_360p.webm", "640x360", "libvpx", "webm", None, 360, "VP8"),
    ("test_vp9_720p.webm", "1280x720", "libvpx-vp9", "webm", None, 720, "VP9"),
    ("test_h264_yuv420p.mp4", "320x240", "libx264", "mp4", "yuv420p", 240, "H264"),
]


@pytest.mark.parametrize("fname,size,vcodec,fmt,pix_fmt,expect_height,expect_codec", VIDEO_CASES)
@pytest.mark.parametrize("func", [get_video_metadata_pyav, get_video_metadata_ffmpeg])
def test_get_video_metadata_all(tmpdir, fname, size, vcodec, fmt, pix_fmt, expect_height, expect_codec, func):
    video_path = os.path.join(tmpdir, fname)
    create_dummy_video(video_path, size=size, vcodec=vcodec, fmt=fmt, pix_fmt=pix_fmt)
    try:
        h, c = func(video_path)
        assert h == expect_height, f"{func.__name__} height mismatch for {video_path}"
        assert c == expect_codec, f"{func.__name__} codec mismatch for {video_path}"
    except ImportError:
        pytest.skip(f"{func.__name__} not available (ImportError)")
