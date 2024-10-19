import streamlit as st
from pytube import YouTube
from PIL import Image
import requests
from io import BytesIO
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.formatters import SRTFormatter

# Streamlit webpage configuration
st.set_page_config(page_title="YouTube Caption, Summarizer, and TTS", layout="wide")

def fetch_video_info(url):
    try:
        yt = YouTube(url)
        return yt.video_id, yt.thumbnail_url, True
    except Exception as e:
        st.error(f"Error fetching video info: {str(e)}")
        return None, None, False

def display_thumbnail(url):
    response = requests.get(url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        st.image(image, caption="Video Thumbnail", use_column_width=True)
    else:
        st.error("Failed to load thumbnail.")

def fetch_captions(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en'])
        formatter = SRTFormatter()
        return formatter.format_transcript(transcript.fetch()), True
    except NoTranscriptFound:
        st.warning("No captions found for this video.")
        return "", False
    except TranscriptsDisabled:
        st.warning("Captions are disabled for this video.")
        return "", False
    except Exception as e:
        st.error(f"An error occurred while fetching captions: {str(e)}")
        return "", False

def main():
    st.title("YouTube Caption, Summarizer, and TTS")
    url = st.text_input("Enter YouTube video URL", "")

    if url:
        video_id, thumbnail_url, video_fetched = fetch_video_info(url)
        if video_fetched:
            display_thumbnail(thumbnail_url)
            captions, captions_fetched = fetch_captions(video_id)
            if captions_fetched:
                st.text_area("Captions", captions, height=300)
            else:
                st.error("Failed to fetch or process captions.")
        else:
            st.error("Failed to fetch video data. Check the provided URL.")

if __name__ == "__main__":
    main()
