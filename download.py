import yt_dlp
import sys
import os

url = sys.argv[1] if len(sys.argv) > 1 else input("Paste TikTok profile URL: ")

username = url.rstrip('/').split('/')[-1].lstrip('@')
output_dir = os.path.expanduser(f"~/Downloads/tiktok/{username}")
os.makedirs(output_dir, exist_ok=True)

ydl_opts = {
    'outtmpl': f'{output_dir}/%(upload_date)s_%(id)s_%(title).50s.%(ext)s',
    'download_archive': f'{output_dir}/downloaded.txt',
    'ignoreerrors': True,
    'quiet': False,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
