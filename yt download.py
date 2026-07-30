# YouTube Video & Audio Downloader
# Requires: yt-dlp
# Install with: python -m pip install yt-dlp

import yt_dlp

def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_playlist(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(playlist)s/%(title)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


while True:
    print("\n===== YouTube Downloader =====")
    print("1. Download Video")
    print("2. Download Audio")
    print("3. Download Playlist")
    print("4. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        url = input("Enter YouTube video URL: ")
        download_video(url)

    elif choice == "2":
        url = input("Enter YouTube video URL: ")
        download_audio(url)

    elif choice == "3":
        url = input("Enter Playlist URL: ")
        download_playlist(url)

    elif choice == "4":
        print("Goodbye!")
        break

    else:
        print("Invalid choice.")