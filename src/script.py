import os
import subprocess
import argparse
import csv
import sys
from pathlib import Path


workingMetaDataTitle = "\FFMETADATAFILE.txt"

videoFile = None
metaDataFile = None
chapterFile = None
subtitleFile = None
thumbnailFile = None




def encaseInQuotes(argument):
    output = '"'+str(argument)+'"'
    return output

# Get Lines from supplied CSV File
def extractCSVLines(csvfile):
    lines = []
    with open(csvfile) as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        for row in csv_reader:
            lines.append(row)
    return lines

# Calculate amount of seconds based on supplied timestamp
def getTimestampsMilliseconds(timestamp):
    # Remove any whitespaces from timestamp
    timestamp = timestamp.replace(" ", "")
    # Get strings between colons of timestamp
    timestamp = timestamp.split(":")
    # Convert list of strings into list of integers (hours/minutes/seconds).
    timestamp = list(map(int, timestamp))

    # Calculate number of seconds in timestamp and multiply by 1000 to get milliseconds.
    seconds = ((timestamp[0] * 3600) + (timestamp[1] * 60) + (timestamp[2]))
    millis = (seconds * 1000)
    return millis

# Add Chapter information to Extracted Metadata File
def addChapterstoMetadata(chapterFile):
    # Initialize an empty list to store the output metadata
    metadata = []
    millis = []
    lines = extractCSVLines(chapterFile)
    total = len(lines)
    count = 0

    # Go through each extracted CSV Line.
    for row in lines:
        # Get milliseconds on timestamp and chapter title.
        milliseconds = getTimestampsMilliseconds(str(row["Timestamp"]))
        title = (str(row["Chapter"].replace(" ", "")))
        # Prepare Metadata Entry Lines.
        meta = ["[CHAPTER]\n", "TIMEBASE=1/1000\n", "START", "END", "title"]
        # IF First Data Line (First Chapter) in CSV File, set start to 0 milliseconds.
        # ELSE set start to the end of previous to the end of the previous milliseconds.
        # Add milliseconds in line to an array.
        if count == 0:
            meta[2] = f'START=0\n'
            millis.append(milliseconds)
        else:
            meta[2] = f'START={milliseconds}\n'
            millis.append(milliseconds)
        # IF Last Data Line in CSV (Last Chapter), set end to milliseconds plus 1.
        # ELSE set end to milliseconds in line..
        if count >= total - 1:
            metadata[count - 1][3] = f'END={milliseconds - 1}\n'
            meta[3] = f'END={milliseconds + 1}\n'
        elif count == 0:
            pass
        else:
            metadata[count - 1][3] = f'END={milliseconds - 1}\n'
        meta[4] = (f'title={title}\n')
        # ADD completed MetaData Entry to Chapter Metadata
        metadata.append(meta)
        count += 1
    # Write Chapter Metadata Entries to extracted metadata file.
    with open(metaDataFile, "a+") as metaDataFile1:
        for x in range(len(metadata)):
            for y in range(len(metadata[x])):
                metaDataFile1.writelines(metadata[x][y])

# SETUP Arguments to be used during program
def setupArgs():
    parser = argparse.ArgumentParser(
        description='Script to Automate Adding Chapters and/or Thumbnails to mp4 files using FFMPEG')

    parser.add_argument('-v', '--video-file', type=str, default=None,
                        help='Specify the filename of the video file')
    parser.add_argument('-c', '--chapter-file', type=str, default=None,
                        help='Specify the filename of the text file containing chapter timestamps')
    parser.add_argument('-t', '--thumbnail-file', type=str, default=None,
                        help='[OPTIONAL] Specify the filename of the image file containing the thumbnail image')
    parser.add_argument('-s','--subtitle-file', type=str,default=None,
                        help='Specify the filename of the srt containing subtitles')
    parser.add_argument('remove', nargs='?', default="None",
                        help="Specify 'remove' to remove the original file after processing.")
    return parser

# RUN command to extract metadata file from video file and set its name to global variable.
def getVideoFileMetadata(videoFile):
    getMetaDataStr = f'ffmpeg -i {encaseInQuotes(videoFile)} -f ffmetadata {encaseInQuotes(metaDataFile)}'
    print(f'Command Used: {getMetaDataStr}')

    cmdResult = subprocess.run(getMetaDataStr)

# GENERATE FFPMEG command to apply Chapters, Subtitle and Thumbnail to video.
def generateCMDCommand(functions):
    """
    A complete command to add Chapters, Subtitle and Thumbnails is:

    ffmpeg -i test.mp4 -i FFMETADATAFILE.txt -i sub.srt -i thumb.jpg -map 3 -map 0 -map_metadata 1 -map 2:s:0
    -codec copy  -c:s mov_text -disposition:0 attached_pic output.mp4

    The first element, input files specifies which files are provided:

    ffmpeg -i test.mp4 -i FFMETADATAFILE.txt -i sub.srt -i thumb.jpg

        Order Should be Video, Chapter, Subtitle, Thumbnail

    The second element, maps streams in input files in the right order:

    -map 3 -map 0 -map_metadata 1 -map 2:s:0

        The Thumbnail should be listed as the first map, the video map should be next and the metadata and subtitle can
        come after that.

    The third element, the codec selection and copy arguments:

    -codec copy  -c:s mov_text -disposition:0 attached_pic output.mp4

        The first argument is for subtitles, the second is for thumbnails, the last is the output file.

    Function will dynamically create a command that is valid regardless of which feature is to be added (all three,
    chapter and thumbnail etc.)
    """

    # Arrays will fill contain the parts of the command, the first element is input, the second is maps the third is
    # copy arguments. Array is filled with empty strings to simplify putting together command.
    chapterCMD = ["", ""]
    subtitleCMD = ["", "", ""]
    thumbnailCMD = ["", "", ""]

    # Generate a Suffix for the Output File that reflects the actions applied to it.
    middle = "_updated-"
    for x in functions:
        middle += x
        middle += "-"
    middle = middle[:-1]

    newFileName = str(videoFile.parent) + "\\" + videoFile.stem + middle + videoFile.suffix

    # IF the specified function is provided fill in the array with commands.
    count = 1
    if 'chapter' in functions:
        chapterCMD[0] = f'-i {encaseInQuotes(metaDataFile)}'
        chapterCMD[1] = f'-map_metadata {count}'
        count += 1
    if 'subtitle' in functions:
        subtitleCMD[0] = f'-i {encaseInQuotes(subtitleFile)}'
        subtitleCMD[1] = f'-map {count}:s:0'
        subtitleCMD[2] = "-c:s mov_text"
        count += 1
    if "thumbnail" in functions:
        thumbnailCMD[0] = f'-i {encaseInQuotes(thumbnailFile)}'
        thumbnailCMD[1] = f'-map {count}'
        thumbnailCMD[2] = "-disposition:0 attached_pic"

    # Create the three elements of the FFMPEG command, if a function is not specified its spots will in the string will
    # blank characters which FFMPEG will ignore.
    input = f'-i {encaseInQuotes(videoFile)} {chapterCMD[0]} {subtitleCMD[0]} {thumbnailCMD[0]}'

    maps = f'{thumbnailCMD[1]} -map 0 {chapterCMD[1]} {subtitleCMD[1]}'

    copyArgs = f'{subtitleCMD[2]} {thumbnailCMD[2]}'

    # Put together command.

    cmd = f'ffmpeg {input} {maps} -c copy {copyArgs} {encaseInQuotes(newFileName)}'

    return cmd



def main():

    # GET arguments.
    parser = setupArgs()
    args = parser.parse_args()

    # CHECK if video file is not provided.
    # CHECK if chapters, subtitle or thumbnail are not provided.
    if args.video_file is None:
        parser.error("Incorrect Usage! A video file must be provided!")
    elif args.chapter_file is None and args.subtitle_file is None and args.thumbnail_file is None:
        parser.error("Atleast one chapter, subtitle, or thumbnail file must be provided!")

    # SET global variables based on arguments provided.
    global videoFile, chapterFile, subtitleFile, thumbnailFile, metaDataFile

    videoFile = Path(args.video_file)
    chapterFile = args.chapter_file
    subtitleFile = args.subtitle_file
    thumbnailFile = args.thumbnail_file
    if not os.path.exists(videoFile):
        print("Invalid video path given. Exiting")
        sys.exit()
    if chapterFile is not None:
        chapterFile = Path(args.chapter_file)
        if not os.path.exists(chapterFile):
            print("Invalid video path given. Exiting")
            sys.exit()
    if subtitleFile is not None:
        subtitleFile = Path(args.subtitle_file)
        if not os.path.exists(subtitleFile):
            print("Invalid video path given. Exiting")
            sys.exit()
    if thumbnailFile is not None:
        thumbnailFile = Path(args.thumbnail_file)
        if not os.path.exists(thumbnailFile):
            print("Invalid video path given. Exiting")
            sys.exit()
    metaDataFile = Path(str(videoFile.parent) + workingMetaDataTitle)

    if args.remove == "remove":
        keepOriginal = False
    else:
        keepOriginal = True

    if chapterFile is not None:
        # Extract FFMPEG Metadata from specified Video File.
        getVideoFileMetadata(videoFile)

        # Update FFMPEG Metadata Text File Using Chapter File specified.
        addChapterstoMetadata(chapterFile)

    # Check if arguments were provided for chapters, subtitles or thumbnails.
    # ADD these to functions and provide functions list to generate FFMPEG command.
    functions = []

    if chapterFile is not None:
        functions.append('chapter')
    if subtitleFile is not None:
        functions.append('subtitle')
    if thumbnailFile is not None:
        functions.append('thumbnail')

    updateCommand = generateCMDCommand(functions)
    print(f'Command Used: {updateCommand}')

    cmdResult = subprocess.run(updateCommand)

    # Rename or Delete the Original Video File
    if keepOriginal:
        newName = videoFile.stem + "_original" + videoFile.suffix

        os.rename(videoFile,newName)
    else:
        os.remove(videoFile)

    print("#####\nStarting Cleanup\n#####")

    if metaDataFile is not None:
        os.remove(metaDataFile)

    print("######")
    print("Process Complete!")
    print("######")

if __name__ == "__main__":
    main()