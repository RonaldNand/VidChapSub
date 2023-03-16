import os
import subprocess
import argparse


def readChapter(chapterFile):
    with open(chapterFile) as f:
        # Read the lines into a list
        lines = f.readlines()
    return lines

# Open the input file
def getTimestampsMilliseconds(timestamp):
    # Remove any whitespaces from timestamp
    timestamp = timestamp.replace(" ", "")
    # Get strings between colons of timestamp
    timestamp = timestamp.split(":")
    # Convert list of strigns into list of integers.
    timestamp = list(map(int, timestamp))

    # Calculate number of seconds in timestamp and multiply by 1000 to get milliseconds.
    seconds = ((timestamp[0] * 60 * 60) + (timestamp[1] * 60) + (timestamp[2]))
    millis = (seconds * 1000)
    return millis

def addChapterstoMetadata(chapterFile,workingMetaDataTitle):
    # Initialize an empty list to store the output metadata
    metadata = []
    target = workingMetaDataTitle
    lines = readChapter(chapterFile)
    total = len(lines)
    count = 0
    # Loop over each line in the input file
    for line in lines:
        # Split the line into timestamp and chapter title
        timestamp = line.strip().split('|')[0]
        title = line.strip().split('|')[1]
        millis = getTimestampsMilliseconds(timestamp)

        # Prepare Metadata fields
        meta = ["[CHAPTER]\n", "TIMEBASE=1/1000\n", "START", "END", "title"]
        # Add starting time to chapter based on timestamp
        meta[2] = (f'START={millis}\n')
        # Add title to chapter based on title provided in line.
        meta[4] = (f'title={title}\n')

        # If MetaData is not the first or last proccessed line, adjust the previous metadata's end value
        # to match start of current metadata
        if not (count == 0 or count > total - 1):
            metadata[count - 1][3] = (f'END={millis}\n')
        # If processing last line, set end value to be 1 millisecond higher than start.
        if count >= total - 1:
            meta[3] = (f'END={millis + 1}\n')

        count += 1

        # Append the chapter metadata to the output list
        metadata.append(meta)

    # Write the output metadata to a file
    # Metadata is a series of lists within a list.
    with open(target, 'a') as f:
        for x in range(len(metadata)):
            for y in range(len(metadata[x])):
                f.writelines(metadata[x][y])

def setupArgs():
    parser = argparse.ArgumentParser(
        description='Script to Automate Adding Chapters and/or Thumbnails to mp4 files using FFMPEG')

    parser.add_argument('-v', '--video-file', type=str, default=None, help='Specify the filename of the video file')
    parser.add_argument('-c', '--chapter-file', type=str, default=None,
                        help='Specify the filename of the text file containing chapter timestamps')
    parser.add_argument('-t', '--thumbnail-file', type=str, default=None,
                        help='[OPTIONAL] Specify the filename of the image file containing the thumbnail image')
    parser.add_argument('remove', nargs='?', default="None",
                        help="Specify 'remove' to remove the original file after processing.")
    return parser


def main():

    parser = setupArgs()
    args = parser.parse_args()

    if args.video_file is None or args.chapter_file is None:
        parser.error("Incorrect Usage! The following options must be provided: -v VideoFileName -c ChapterTimestampsFile")

    workingMetaDataTitle = "FFMETADATAFILE.txt"
    videoFile = args.video_file
    chapterFile = args.chapter_file
    thumbFile = args.thumbnail_file
    if args.remove == "remove":
        keepOriginal = False
    else:
        keepOriginal = True

    # Extract FFMPEG Metadata from specified Video File.

    getMetaData = [
        "ffmpeg",
        "-i", videoFile,
        "-f","ffmetadata",
        workingMetaDataTitle
    ]

    cmdResult = subprocess.run(getMetaData, stdout=True,text=True, check=True)

    print("######")
    print("Metadata Extraction Complete")
    print("######")

    # Update FFMPEG Metadata Text File Using Chapter File specified.

    addChapterstoMetadata(chapterFile,workingMetaDataTitle)

    print("######")
    print("Chapters Added to MetaData File")
    print("######")

    # Apply Updated FFMPEG Metadata Text File to Video File

    chapOutput = videoFile[:-4] + "_chaptersAdded" + videoFile[-4:]

    applyUpdatedMetaData = [
        "ffmpeg",
        "-i", videoFile,
        "-i", workingMetaDataTitle,
        "-c", "copy",
        "-map_metadata", "1",
        chapOutput
    ]

    cmdResult = subprocess.run(applyUpdatedMetaData, stdout=True,text=True, check=True)

    print("######")
    print("Updated Metadata Succesfully Added")
    print("######")

    # Rename or Delete the Original Video File
    if keepOriginal:
        newName = videoFile[:-4] + "_original" + videoFile[-4:]
        os.rename(videoFile,newName)
    else:
        os.remove(videoFile)

    #If no Thumbnail File was specified rename and finish. Else add Thumbnail to VideoFile.
    if thumbFile == None:
        os.rename(chapOutput,videoFile)
        print("######")
        print("Output File Succesfully Renamed")
        print("######")
    else:
        # Apply Custom Thumbnail to Outputed Video File
        print("Applying Custom Thumbnail to Metadata")
        thumbOutput = videoFile[:-4] + "_thumbnailAdded" + videoFile[-4:]
        applyUpdatedThumbnail = [
            "ffmpeg",
            "-i", chapOutput,
            "-i", thumbFile,
            "-map", "1",
            "-map", "0",
            "-c", "copy",
            "-disposition:0", "attached_pic",
            thumbOutput
        ]
        cmdResult = subprocess.run(applyUpdatedThumbnail, stdout=True,text=True, check=True)
        print("######")
        print("Custom Thumbnail Applied succesfully")
        print("######")

        # Remove Original Output File and Rename
        os.remove(chapOutput)
        os.rename(thumbOutput, videoFile)
        print("######")
        print("Output File Succesfully Renamed")
        print("######")

    print("#####\nStarting Cleanup\n#####")

    os.remove(workingMetaDataTitle)

    print("######")
    print("Process Complete!")
    print("######")

if __name__ == "__main__":
    main()