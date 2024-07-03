import streamlit as st # type: ignore
from pytube import YouTube, Playlist
import ffmpeg 
import os
import zipfile
from io import BytesIO
import shutil
from youtube_transcript_api import YouTubeTranscriptApi # type: ignore
from youtube_transcript_api.formatters import SRTFormatter # type: ignore


st.title('OE Video Tool')
# Your script logic here

# Global Variables

Audio_Path = "./Downloaded_Audio"
Video_Path = "./Downloaded_Video"
files_to_download = {}


# Custom Functions

def clean(title):
    trans_table = str.maketrans('','',":'")
    cleaned_string = title.translate(trans_table)
    return cleaned_string

def get_captions(video_url):
    yt = YouTube(video_url)
    try:
        got = YouTubeTranscriptApi.get_transcript(yt.video_id, languages=['en'])
        #st.write("Got the captions!")
        file_name = clean(yt.title)+".srt"
        #st.write(file_name)
        f = open("Captions/"+file_name, "w")
        formatter = SRTFormatter()
        srt_transcript = formatter.format_transcript(got)
        f.write(srt_transcript)
        f.close()
        return file_name
    except Exception: 
        st.write("No English captions available")

def get_ITAG(url):
    yt = YouTube(url)
    top_itag = yt.streams.order_by("resolution").last().itag
    return(top_itag)


def is_playlist(url):
    try:
        # Attempt to create a Playlist object
        playlist = Playlist(url)
        # Check if the playlist object has videos
        if len(playlist.video_urls) > 0:
            return True
    except Exception as e:
        # If an exception occurs, it means the URL is not a playlist
        pass
        return False



def add_to_dict(file_name):
    file_path = Video_Path.replace("./","")+"/" + file_name
    files_to_download[file_name] = file_path
    #st.write(f"Added {file_name}")

def add_to_dict_srt(file_name):
    file_path = "Captions/" + file_name
    files_to_download[file_name] = file_path
    #st.write(f"Added {file_name}")


def download_youtube_video(video_url, capt):
    try:
        # Create Youtube Object
        yt = YouTube(video_url)
        st.write(f"Got the video: {yt.title}")
        # Get highest Resolution streams
        audio = yt.streams.filter(only_audio=True).first()
        best_itag = get_ITAG(video_url)
        stream = yt.streams.get_by_itag(best_itag)
        st.write(f"Best Stream is {stream}")
        # Download Video and Audio Components
        with st.spinner("Downloading Video Components..."):
            audio.download(Audio_Path)
            st.write("Audio Downloaded")
            stream.download(output_path=Video_Path)
            st.write("Video Downloaded")
        # Label the components
        ext = stream.mime_type.replace("video/",'.')
        video_title = 'Downloaded_Video/'+clean(stream.title)+ext
        audio_title = 'Downloaded_Audio/'+clean(audio.title)+'.mp4'
        Video_Stream = ffmpeg.input(video_title)
        Audio_Stream = ffmpeg.input(audio_title)
        # Combine High Quality Audio and Video
        output_path =clean(stream.title)+'_'+stream.resolution+'.mp4'
        with st.spinner("Combining Components..."):
            ffmpeg.output(Video_Stream, Audio_Stream,  'Downloaded_Video/'+output_path, vcodec='copy', acodec='aac', loglevel="quiet").run()
            os.remove(audio_title)
            os.remove(video_title)
        st.write("Done!")
        if capt:
            #Create captions srt file
            os.mkdir("./Captions")
            caption_file = get_captions(video_url)
            #Save Video and captions file to zip
            zip_buffer = BytesIO()
            add_to_dict(output_path)
            if caption_file != None:
                add_to_dict_srt(caption_file)
            with zipfile.ZipFile(zip_buffer,"w") as zip_file:
                for file_name, file_path in files_to_download.items():
                    zip_file.write(file_path, arcname=file_name)
            zip_buffer.seek(0)
            st.download_button(label="Download Zip",data = zip_buffer, file_name=yt.title+'.zip', mime='application/zip')
            # Display file to download
            st.write(f"Files being Downloaded are:")
            for x in files_to_download.keys():
                st.write(f"    {x}")
        else: 
            with open('Downloaded_Video/'+output_path, 'rb') as video_file:
                video_bytes = video_file.read()
            video_buffer = BytesIO(video_bytes)
            st.download_button(label="Download Highest Resolution Youtube Video",data = video_buffer, file_name=output_path, mime='video/mp4')
        # Clearing Server Memory
        if os.path.exists(Audio_Path):
            shutil.rmtree(Audio_Path)
        if os.path.exists(Video_Path):
            shutil.rmtree(Video_Path)
        if os.path.exists("./Captions"):
            shutil.rmtree("./Captions")
    except Exception as e:
        st.write(f"Error occurred:{e}")


def download_youtube_playlist(video_url, capt):
    try:
        # Create Playlist Object
        pl = Playlist(video_url)
        zip_buffer = BytesIO()
        st.write(f"Got the playlist: {pl.title}")
        if capt:
            os.mkdir("./Captions")
        for index, video_url in enumerate(pl.video_urls):
            try:
                with st.spinner("Getting Playlist"):
                    st.write(f"Working on video {index+1}")
                    # Create Youtube Object
                    yt = YouTube(video_url)
                    st.write(f"Got the video: {yt.title}")
                    # Get highest Resolution streams
                    audio = yt.streams.filter(only_audio=True).first()
                    best_itag = get_ITAG(video_url)
                    stream = yt.streams.get_by_itag(best_itag)
                    #st.write(f"Best Stream is {stream}")
                    # Download Video and Audio Components
                    with st.spinner("Downloading Video Components..."):
                        audio.download(Audio_Path)
                        st.write("Audio Downloaded")
                        stream.download(output_path=Video_Path)
                        st.write("Video Downloaded")
                    # Label the components
                    ext = stream.mime_type.replace("video/",'.')
                    video_title = 'Downloaded_Video/'+clean(stream.title)+ext
                    audio_title = 'Downloaded_Audio/'+clean(audio.title)+'.mp4'
                    Video_Stream = ffmpeg.input(video_title)
                    Audio_Stream = ffmpeg.input(audio_title)
                    # Combine High Quality Audio and Video
                    output_path =clean(stream.title)+'_'+stream.resolution+'.mp4'
                    with st.spinner("Combining Components..."):
                        ffmpeg.output(Video_Stream, Audio_Stream,  'Downloaded_Video/'+output_path, vcodec='copy', acodec='aac', loglevel="quiet").run()
                        os.remove(audio_title)
                        os.remove(video_title)
                    st.write(f"Video {index+1} completed")
                    if capt:
                        #Create captions srt file
                        caption_file = get_captions(video_url)
                        if caption_file != None:
                            add_to_dict_srt(caption_file)
                    add_to_dict(output_path)
            except Exception as e:
                st.write(f"Error occurred:{e}")
        st.write("Playlist is Done!")
        # Display file to download
        st.write(f"Files being Downloaded are:")
        for x in files_to_download.keys():
            st.write(f"    {x}")
        # Creating zip
        with zipfile.ZipFile(zip_buffer,"w") as zip_file:
            for file_name, file_path in files_to_download.items():
                zip_file.write(file_path, arcname=file_name)
        zip_buffer.seek(0)
        st.download_button(label="Download Zip",data = zip_buffer, file_name=pl.title+'.zip', mime='application/zip')
        # Clearing Server Memory
        if os.path.exists(Audio_Path):
            shutil.rmtree(Audio_Path)
        if os.path.exists(Video_Path):
            shutil.rmtree(Video_Path)
        if os.path.exists("./Captions"):
            shutil.rmtree("./Captions")
    except Exception as e:
        st.write(f"Error occurred:{e}")



def main():
    submitted=False
    want_capt = False
    submitted_password = False
    with st.form("Password Input"):
        entered_password = st.text_input(label = "Password:", value="", type="password")
        submitted_password = st.form_submit_button("Submit")
    if (entered_password == st.secrets["Master_Password"] or entered_password in st.secrets["Pws"]) and submitted_password:
        if entered_password in st.secrets["Pws"]:
            chosen_index = st.secrets["Pws"].index(entered_password)
            user_name = st.secrets["Approved_users"][chosen_index]
            st.write(f"Welcome {user_name}")
        with st.form("Input Form"):
            want_capt = st.toggle(label="Generate Captions?")
            url = st.text_input(label="URL input", value="")
            submitted = st.form_submit_button("Submit")
        if(submitted):
            try:
                if is_playlist(url):
                    st.write("This is a playlist")
                    download_youtube_playlist(url, want_capt)
                else:
                    download_youtube_video(url, want_capt)
            except Exception as e:
                st.write(f"An error occurred:{e}")
    else:
        if not submitted_password:
            st.write("Incorrect Password")

    
    



if __name__ == '__main__':
    main()
