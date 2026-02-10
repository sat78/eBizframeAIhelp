from moviepy import VideoFileClip, VideoClip
print(f"Has subclipped? {hasattr(VideoClip, 'subclipped')}")
print(f"Has subclip? {hasattr(VideoClip, 'subclip')}")
print(f"Has with_subclip? {hasattr(VideoClip, 'with_subclip')}")
