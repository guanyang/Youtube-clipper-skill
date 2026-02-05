#!/usr/bin/env python3
"""
下载 YouTube 视频和字幕
使用 yt-dlp 下载视频（最高 1080p）和英文字幕
"""

import sys
import json
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("❌ Error: yt-dlp not installed")
    print("Please install: pip install yt-dlp")
    sys.exit(1)

from utils import (
    validate_url,
    sanitize_filename,
    format_file_size,
    get_video_duration_display,
    ensure_directory,
)


def download_video(url: str, output_dir: str = None) -> dict:
    """
    下载 YouTube 视频和字幕

    Args:
        url: YouTube URL
        output_dir: 输出目录，默认为当前目录

    Returns:
        dict: {
            'video_path': 视频文件路径,
            'subtitle_path': 字幕文件路径,
            'title': 视频标题,
            'duration': 视频时长（秒）,
            'file_size': 文件大小（字节）
        }

    Raises:
        ValueError: 无效的 URL
        Exception: 下载失败
    """
    # 验证 URL
    if not validate_url(url):
        raise ValueError(f"Invalid YouTube URL: {url}")

    # 设置输出目录
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    output_dir = ensure_directory(output_dir)

    print(f"🎬 开始下载视频...")
    print(f"   URL: {url}")
    print(f"   输出目录: {output_dir}")

    # 配置 yt-dlp 选项
    # 检查是否存在 cookies.txt
    cookies_file = output_dir / "cookies.txt"
    if not cookies_file.exists():
        # 尝试在上级目录查找
        cookies_file = Path.cwd() / "cookies.txt"

    # 基础配置
    ydl_opts = {
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
        "subtitlesformat": "vtt",
        "writethumbnail": False,
        "quiet": False,
        "no_warnings": False,
        "progress_hooks": [_progress_hook],
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
    }

    # 配置 Cookie 策略
    if cookies_file.exists():
        print(f"🍪 使用 cookies.txt: {cookies_file.name}")
        ydl_opts["cookiefile"] = str(cookies_file)
    else:
        print("🍪 尝试从 Chrome 浏览器获取 Cookies...")
        print("   ⚠️  注意: macOS 可能会弹出窗口请求访问 'Chrome Safe Storage'")
        print("   ⚠️  请点击 '始终允许' 或 '允许'，否则脚本将卡住")
        ydl_opts["cookiesfrombrowser"] = ("chrome",)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 提取信息
            print("\n📊 获取视频信息...")
            info = ydl.extract_info(url, download=False)

            title = info.get("title", "Unknown")
            duration = info.get("duration", 0)
            video_id = info.get("id", "unknown")

            print(f"   标题: {title}")
            print(f"   时长: {get_video_duration_display(duration)}")
            print(f"   视频ID: {video_id}")

            # 下载视频
            print(f"\n📥 开始下载...")
            info = ydl.extract_info(url, download=True)

            # 获取下载的文件路径
            video_filename = ydl.prepare_filename(info)
            video_path = Path(video_filename)

            # 查找字幕文件
            subtitle_path = None
            subtitle_exts = [".en.vtt", ".vtt"]
            for ext in subtitle_exts:
                potential_sub = video_path.with_suffix(ext)
                # 处理带语言代码的字幕文件
                if not potential_sub.exists():
                    # 尝试 <filename>.en.vtt 格式
                    stem = video_path.stem
                    potential_sub = video_path.parent / f"{stem}.en.vtt"

                if potential_sub.exists():
                    subtitle_path = potential_sub
                    break

            # 获取文件大小
            file_size = video_path.stat().st_size if video_path.exists() else 0

            # 验证下载结果
            if not video_path.exists():
                raise Exception("Video file not found after download")

            print(f"\n✅ 视频下载完成: {video_path.name}")
            print(f"   大小: {format_file_size(file_size)}")

            if subtitle_path and subtitle_path.exists():
                print(f"✅ 字幕下载完成: {subtitle_path.name}")
            else:
                print(f"⚠️  未找到英文字幕")
                print(f"   提示：某些视频可能没有字幕或需要自动生成")

            return {
                "video_path": str(video_path),
                "subtitle_path": str(subtitle_path) if subtitle_path else None,
                "title": title,
                "duration": duration,
                "file_size": file_size,
                "video_id": video_id,
            }

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 下载失败: {error_msg}")

        # 提供针对性建议
        if (
            "Sign in to confirm" in error_msg
            or "Requested format is not available" in error_msg
            or "Only images are available" in error_msg
        ):
            print("\n💡 建议解决方案:")
            print("1. 确保 Chrome 浏览器已关闭（yt-dlp 需要访问 Cookie 数据库）")
            print("2. 推荐：手动导出 Cookies 文件")
            print("   a. 在 Chrome 安装 'Get cookies.txt LOCALLY' 插件")
            print("   b. 访问 YouTube 并登录")
            print("   c. 点击插件导出 cookies.txt")
            print(f"   d. 将文件保存到: {output_dir}/cookies.txt")
            print("   e. 重新运行此脚本")

        raise


def _progress_hook(d):
    """下载进度回调"""
    if d["status"] == "downloading":
        # 显示下载进度
        if "downloaded_bytes" in d and "total_bytes" in d and d["total_bytes"]:
            percent = d["downloaded_bytes"] / d["total_bytes"] * 100
            downloaded = format_file_size(d["downloaded_bytes"])
            total = format_file_size(d["total_bytes"])
            speed = d.get("speed", 0)
            speed_str = format_file_size(speed) + "/s" if speed else "N/A"

            # 使用 \r 实现进度条覆盖
            bar_length = 30
            filled = int(bar_length * percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)

            print(
                f"\r   [{bar}] {percent:.1f}% - {downloaded}/{total} - {speed_str}",
                end="",
                flush=True,
            )
        elif "downloaded_bytes" in d:
            # 无总大小信息时，只显示已下载
            downloaded = format_file_size(d["downloaded_bytes"])
            speed = d.get("speed", 0)
            speed_str = format_file_size(speed) + "/s" if speed else "N/A"
            print(f"\r   下载中... {downloaded} - {speed_str}", end="", flush=True)

    elif d["status"] == "finished":
        print()  # 换行


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("Usage: python download_video.py <youtube_url> [output_dir]")
        print("\nExample:")
        print("  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM")
        print(
            "  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM ~/Downloads"
        )
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = download_video(url, output_dir)

        # 输出 JSON 结果（供其他脚本使用）
        print("\n" + "=" * 60)
        print("下载结果 (JSON):")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
