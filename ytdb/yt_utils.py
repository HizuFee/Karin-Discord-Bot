"""Youtube Utils
    - Downloads youtube video by url or search???

"""
import asyncio
import yt_dlp as youtube_dl

# async def download_audio_from_url(url, output_path='.', audio_format='mp3'):
#     """
#     Downloads audio from a given URL using yt-dlp.

#     Args:
#         url (str): The URL of the video or audio source.
#         output_path (str): The directory to save the downloaded audio.
#         audio_format (str): The desired audio format (e.g., 'mp3', 'm4a', 'wav').
#     """
#     filename = f'{output_path}/{uuid.uuid4().hex()}'  # Generate a unique filename
#     ydl_opts = {
#         'format': 'bestaudio/best',  # Select the best audio format
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': audio_format,
#             'preferredquality': '192',  # Set preferred audio quality
#         }],
#         'outtmpl': filename,  # Output template
#         'noplaylist': True,  # Don't download entire playlists
#     }

#     try:
#         with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([url])
#             ydl.extract_info(url, download=False)
#         print(f"Audio downloaded successfully to {output_path} in {audio_format} format.")
#         return {
#         "id": data["id"],
#         "file": filename,
#         "title": data["title"],
#         "url": data["webpage_url"],
#     }
#     except Exception as e:
#         print(f"An error occurred: {e}")

async def download(url_or_string: str, tag: str = "unknown") -> str:
    """Download from url or search string????

    Arguments:
        url_or_string (str): The url of the youtube video or search???
    """

    # Setup options
    # youtube_dl.utils.bug_reports_message = lambda: ""
    ydl_opts = {
        'format': 'bestaudio/best',  # Select the best audio format
        # 'postprocessors': [{
        #     'key': 'FFmpegExtractAudio',
        #     'preferredcodec': 'mp3',
        #     'preferredquality': '192',  # Set preferred audio quality
        # }],
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'outtmpl': '%(title)s.%(ext)s',  # Output template
        'noplaylist': True,  # Don't download entire playlists
    }
    ytdl = youtube_dl.YoutubeDL(ydl_opts)

    # Go and download based off of url_or_string in background
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None, lambda: ytdl.extract_info(url_or_string, download=True)
    )

    if "entries" in data:
        # take first item from a playlist
        data = data["entries"][0]

    # Create file and return information
    filename = ytdl.prepare_filename(data)
    
    # Extract thumbnail URL (prefer highest quality available)
    thumbnail = None
    if "thumbnail" in data and data["thumbnail"]:
        thumbnail = data["thumbnail"]
    elif "thumbnails" in data and data["thumbnails"]:
        # Get the highest quality thumbnail from the list
        thumbnails = data["thumbnails"]
        if thumbnails:
            # Sort by width/height if available, or take the last one (usually highest quality)
            thumbnail = thumbnails[-1].get("url") if isinstance(thumbnails[-1], dict) else None
    
    # Format duration if available
    duration_str = None
    if "duration" in data and data["duration"]:
        duration_seconds = data["duration"]
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        if hours > 0:
            duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            duration_str = f"{minutes}:{seconds:02d}"
    
    return {
        "id": data["id"],
        "file": filename,
        "title": data["title"],
        "url": data["webpage_url"],
        "thumbnail": thumbnail,
        "duration": duration_str,
        "uploader": data.get("uploader"),
    }


if __name__ == "__main__":
    URL = str(input("Enter the URL of the video: \n>>"))
    # DEST = (
    #     str(input("Enter the destination (leave blank for current directory) \n>>"))
    #     or "."
    # )
    asyncio.run(download(URL))
