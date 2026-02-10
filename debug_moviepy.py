from moviepy import VideoFileClip, VideoClip
print("VideoFileClip methods:")
print([m for m in dir(VideoFileClip) if "sub" in m])
print("VideoClip methods:")
print([m for m in dir(VideoClip) if "sub" in m])
