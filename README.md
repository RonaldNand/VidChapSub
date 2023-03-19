# VidChapSub

**Purpose:**

Add Chapters, Subtitles and Thumbnails to video files using FFMPEG commands.

This program will convert supplied chapter input into valid FFMPEG Metadata and add Subtitle, and Thumbnail streams to a video file. The program will operate if any combination of the three is provided (e.g. Chapter File, Chapter + Thumbnail, Subtitle + Thumbnail)

An valid FFMPEG command will be generated regardless of combination. 

**Requirements:**

Python 3.11

FFMPEG

**Usage:**

The following inputs can be used:

Video: Any video file compatible with FFMPEG.

Chapter: Chapters in CSV format.

Subtitle: Subtitle in srt format

Thumbnail: Any common image format (eg. jpg,png)

The command 
