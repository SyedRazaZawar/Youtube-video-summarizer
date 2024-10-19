import streamlit as st
from pytube import YouTube
from PIL import Image
import requests
from io import BytesIO
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.formatters import SRTFormatter

# API URLs and headers for Hugging Face
API_URL_SUMMARIZATION = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
API_URL_TTS = "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_vits"
headers = {"Authorization": "Bearer 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"}

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
        response = requests.post(API_URL_SUMMARIZATION, headers=headers, json={"inputs": text, "parameters": {"min_length": min_length, "max_length": max_length}})
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API error: {response.status_code}, {response.text}")
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
            st.error(f"API error: {response.status_code}, {response.text}")
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

                # Button to trigger summarization
                summarize_button = st.button("Summarize Captions")
                if summarize_button or st.session_state.get('summary_requested', False):
                    st.session_state['summary_requested'] = True  # Persist state across reruns
                    with st.spinner('Summarizing...'):
                        output = query_summarization_api(captions, min_length, max_length)
                        if output and 'summary_text' in output:
                            summary = output['summary_text']
                            st.text_area("Summary", summary, height=200)

                            # Button to trigger TTS
                            tts_button = st.button("Generate Audio for Summary")
                            if tts_button:
                                with st.spinner('Generating audio...'):
                                    audio_data = query_tts_api(summary)
                                    if audio_data:
                                        audio_file_path = "summary_audio.wav"
                                        with open(audio_file_path, "wb") as f:
                                            f.write(audio_data)
                                        st.audio(audio_file_path)
                                        st.download_button("Download Audio", audio_data, file_name="summary_audio.wav", mime="audio/wav")
        else:
            st.error("Failed to fetch video data. Check the provided URL.")

if __name__ == "__main__":
    main()
