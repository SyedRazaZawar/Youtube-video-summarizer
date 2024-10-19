import streamlit as st
from pytube import YouTube
from PIL import Image
import requests
from io import BytesIO
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.formatters import SRTFormatter

# API URLs and headers for Hugging Face
API_URL_SUMMARIZATION = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
API_URL_TTS = "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_vits"
headers = {"Authorization": "Bearer your_hf_API_token"}  # Replace 'your_hf_API_token' with your actual token.

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
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            st.image(image, caption="Video Thumbnail", use_column_width=True)
    except Exception as e:
        st.error(f"Failed to display thumbnail: {str(e)}")

def fetch_captions(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en'])
        formatter = SRTFormatter()
        return formatter.format_transcript(transcript.fetch()), True
    except (NoTranscriptFound, TranscriptsDisabled):
        st.warning("No available captions or transcripts are disabled for this video.")
        return "", False
    except Exception as e:
        st.error(f"An error occurred while fetching captions: {str(e)}")
        return "", False

def query_summarization_api(text, min_length, max_length):
    try:
        json_payload = {
            "inputs": text,
            "parameters": {
                "min_length": min_length,
                "max_length": max_length,
                "do_sample": False  # Ensure deterministic outputs
            }
        }
        response = requests.post(API_URL_SUMMARIZATION, headers=headers, json=json_payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to call summarization API: {str(e)}")
        return None

def query_tts_api(text):
    try:
        response = requests.post(API_URL_TTS, headers=headers, json={"inputs": text})
        if response.status_code == 200:
            return response.content  # Binary audio data
        else:
            st.error(f"API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to call TTS API: {str(e)}")
        return None

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

                min_length = st.sidebar.slider("Min Length", 10, 500, 50)
                max_length = st.sidebar.slider("Max Length", 50, 1000, 200)

                if st.button("Summarize Captions"):
                    with st.spinner('Summarizing...'):
                        output = query_summarization_api(captions, min_length, max_length)
                        if output and 'summary_text' in output:
                            st.text_area("Summary", output['summary_text'], height=200)
                        else:
                            st.error("Failed to get a valid response from the summarization API.")

        else:
            st.error("Failed to fetch video data. Check the provided URL.")

if __name__ == "__main__":
    main()
