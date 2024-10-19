import streamlit as st
from pytube import YouTube
from PIL import Image
import requests
from io import BytesIO
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.formatters import SRTFormatter
import time

# Define exponential backoff
def retry_with_exponential_backoff(func, max_retries=5, initial_wait=0.5, backoff_factor=2):
    wait_time = initial_wait
    retries = 0
    while retries < max_retries:
        try:
            return func()
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            retries += 1
            time.sleep(wait_time)
            wait_time *= backoff_factor
            if retries == max_retries:
                st.error(f"Failed to fetch captions after {max_retries} attempts.")
                return None
            else:
                st.warning("Retrying to fetch captions...")

# Function to fetch captions with retries
def fetch_captions_with_retries(video_id, language_code='en'):
    def fetch():
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript([language_code])
        formatter = SRTFormatter()
        return formatter.format_transcript(transcript.fetch())
    
    return retry_with_exponential_backoff(fetch)

# Modify the main function to use fetch_captions_with_retries
def main():
    st.title("YouTube Caption, Summarizer, and TTS")
    # [The rest of your Streamlit code remains the same]

    # Fetch and store captions in session state with retries
    if st.button("Fetch Video Info"):
        if url:
            video_id, thumbnail_url = fetch_video_info(url)
            if video_id:
                st.session_state['video_id'] = video_id
                available_languages = fetch_available_languages(video_id)
                if available_languages:
                    st.session_state['available_languages'] = available_languages
                    language_options = list(available_languages.values())
                    selected_language = st.selectbox("Select Caption Language", language_options)
                    selected_language_code = list(available_languages.keys())[language_options.index(selected_language)]
                    captions = fetch_captions_with_retries(video_id, selected_language_code)
                    if captions:
                        st.session_state['captions'] = captions
                        st.session_state['summary'] = ""  # Reset summary when new captions are fetched
                    else:
                        st.error("Failed to fetch captions in the selected language.")
                else:
                    st.warning("No available captions for this video.")
            else:
                st.error("Failed to fetch video data. Check the provided URL.")

# Include the retry mechanism wherever you are calling API functions that might fail.

if __name__ == "__main__":
    main()
