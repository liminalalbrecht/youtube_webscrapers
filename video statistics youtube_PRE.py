##### Goal: Retrieve videos of selected Youtube-channels including the meta-data


### (I) Setup
# (Ia) Imports
# install packages in terminal beforehand
# imports the packages (i.e., sub-programmes) needed to perform the subsequent tasks
import pandas as pd
from googleapiclient.discovery import build
import json

# (Ib) API-Key
# API-Key is necessary to use the YouTube-API
# API-Key can be registered under: https://console.developers.google.com/
API_KEY = "XXX"

# (Ic) Channel_IDs
# Channel ID: We have to state which channels we want to web scrape
# therefore, we use channel IDs (i.e., unique identifier of a channel)
# the channel IDs of a youtube account can be acquired either:
# via this website: https://commentpicker.com/youtube-channel-id.php
# or by inspecting the channel website and searching for this string in the html: https://www.youtube.com/channel
# add channel by adding name and ID, seperated by a comma

account_selection = {
    "name_of_channel": "ID_of_Channel"}


# (Id) Connection to YouTube API
# this code chunk "connects" to the YouTube data interface
resource = build("youtube", "v3", developerKey=API_KEY)


# (Ie) create empty objects that will be filled later with the data
channel_name = []
channel_identity = []
video_title = []
published = []
video_id = []

dictionary_yt = {
    "channel_name": channel_name,
    "channel_id": channel_identity,
    "video_title": video_title,
    "published": published,
    "video_id": video_id}

df_videos = pd.DataFrame(dictionary_yt)
df_videos.info()

video_id_statistics = []
duration = []
viewCount = []
likeCount = []
commentCount = []

dictionary_stata = {
    "video_id": video_id_statistics,
    "duration": duration,
    "view_count": viewCount,
    "like_count": likeCount,
    "comment_count": commentCount}

df_stata = pd.DataFrame(dictionary_stata)
df_stata.info()

upload_list = []





### (II) API scripts

# 4 Step-approach:
# (a) get a list of the uploaded videos for each channel
# (b) retrieve the video IDs for all the videos of the list
# (c) get video statistics for each video
# (d) merge data table of step b and c


## (IIa): Get each channel's list of uplodaded videos

for key, value in account_selection.items():
    request = resource.channels().list(
        part="contentDetails",
        id=value)

    response = request.execute()
    items = response["items"]

    for item in items:
        detail = item["contentDetails"]
        content_details = detail["relatedPlaylists"]
        upload_id = content_details["uploads"]

        upload_list.append(upload_id)

#soundness check
print(upload_list)
print(len(upload_list))





## (IIb): find video ID for each video in the list of videos
# each video has a unique ID, we need the ID to download the meta data later on
#important: you need to set the date for how far you want to go back in time
#e.g., if you want to retrieve all videos from today until January 1st, 2023, you need to set the data ('set_date' in in the codee line 133) to "2023-01-01T00:00:00Z"

next_page_token = ""
video_count = 0
set_date = "2023-01-30T00:00:00Z"

for entry in upload_list:
    while True:
        request_2 = resource.playlistItems().list(
            part="contentDetails,snippet",
            maxResults=50,
            playlistId=entry,
            pageToken=next_page_token
        )

        response_2 = request_2.execute()
        #print(json.dumps(response_2, indent=2))

        item_2 = response_2["items"]

        video_count += len(response_2["items"])
        print(f"video count: {video_count}")

        for item in item_2:
            item_info = item["snippet"]
            published_date = item_info["publishedAt"]

            if published_date >= set_date:
                pass
            else:
                print("End of Item list")
                break

            channelID = item_info["channelId"]
            channelNAME = item_info["channelTitle"]
            title = item_info["title"]
            ressourceID = item_info["resourceId"]
            videoID = ressourceID["videoId"]
            next_page_token = response_2["nextPageToken"]

            length = len(df_videos)
            df_videos.loc[length] = [channelNAME, channelID, title, published_date, videoID]

        if published_date >= set_date:
            print("Next Token")
            continue
        else:
            next_page_token = ""
            print("Next Channel")
            break


#soundness check
df_videos.info()
df_videos.head()
df_videos.head(-5)
df_videos.shape
print(df_videos[["published", "video_title"]].head(-30))
df_videos.groupby("channel_name").count()

#print(response_2)
#print(json.dumps(response_2, indent=2))




## (IIc): retrieve video statistics (i.e., meta-data) for each video

for label, content in df_videos.iterrows():
    request_3 = resource.videos().list(
        part="statistics,contentDetails",
        id=content["video_id"])

    response_3 = request_3.execute()
    item_3 = response_3["items"]

    for item in item_3:
        details_content = item["contentDetails"]
        length_video = details_content["duration"]

        video_identification = item["id"]
        statistics_over = item["statistics"]
        view_C = statistics_over["viewCount"]
        like_C = statistics_over["likeCount"]

        if statistics_over.get("commentCount"):
            comment_C = statistics_over["commentCount"]
        else:
            comment_C = "NaN"
            print(f"comments disabled for {video_identification}")

        length = len(df_stata)
        df_stata.loc[length] = [video_identification, length_video, view_C, like_C, comment_C]


#soundness check
df_stata.info()
df_stata.head()
df_stata.shape

#print(response)
#print(json.dumps(response_3, indent=2))




## (IId): merge tables that resulted from step (IIb) and (IIc)
# also, do some data wrangling to prepare the data

#merge tables
dataframe_video = df_videos.merge(df_stata, on="video_id", validate="one_to_one")

#soundness check
dataframe_video.head(20)
dataframe_video.columns
dataframe_video.shape
dataframe_video.info()



#data wrangling:
#drop duplicates
dataframe_video.drop_duplicates()

#transform into correct data types:
dataframe_video["view_count"] = dataframe_video["view_count"].astype(float)
dataframe_video["like_count"] = dataframe_video["like_count"].astype(float)
dataframe_video["comment_count"] = dataframe_video["comment_count"].astype(float)

from datetime import datetime
dataframe_video["published"] = pd.to_datetime(dataframe_video["published"], format="%Y-%m-%d %H:%M:%S")
dataframe_video["published"] = dataframe_video["published"].dt.strftime("%Y-%m-%d")

#duration into seconds
import isodate
for row_label, row_data in dataframe_video.iterrows():
    dataframe_video.loc[row_label, "duration"] = isodate.parse_duration(row_data["duration"])



### (III) save as excel
from datetime import date
dataframe_video.to_excel(f'videos_statistics_{date.today()}.xlsx', sheet_name='video_infos')




















