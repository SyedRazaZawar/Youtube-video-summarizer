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
headers = {"Authorization": "Bearer your_huggingface_api_key_here"}

# Streamlit webpage configuration
st.set_page_config(page_title="YouTube Caption, Summarizer, and TTS", layout="wide")

def fetch_video_info(url):
    try:
        yt = YouTube(url)
        return yt.video_id, yt.thumbnail_url
    except Exception as e:
        st.error(f"Error fetching video info: {str(e)}")
        return None, None

def display_thumbnail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            st.image(image, caption="Video Thumbnail", use_column_width=True)
        else:
            st.warning("Failed to load thumbnail.")
    except Exception as e:
        st.error(f"Failed to display thumbnail: {str(e)}")

def fetch_captions(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        languages = [transcript.language_code for transcript in transcript_list]
        if 'en' in languages:
            transcript = transcript_list.find_transcript(['en'])
            formatter = SRTFormatter()
            return formatter.format_transcript(transcript.fetch()), 'en'
        elif languages:
            transcript = transcript_list.find_transcript(languages[0])
            formatter = SRTFormatter()
            return formatter.format_transcript(transcript.fetch()), languages[0]
        else:
            st.error("Transcripts found but no accessible languages.")
            return "", None
    except NoTranscriptFound:
        st.error("No transcripts available for this video.")
        return "", None
    except TranscriptsDisabled:
        st.error("Transcripts are disabled for this video.")
        return "", None
    except Exception as e:
        st.error(f"An error occurred while fetching captions: {str(e)}")
        return "", None

def query_summarization_api(text, min_length, max_length):
    try:
        response = requests.post(API_URL_SUMMARIZATION, headers=headers, json={"inputs": text, "parameters": {"min_length": min_length, "max_length": max_length}})
        return response.json()
    except Exception as e:
        st.error(f"Failed to call summarization API: {str(e)}")
        return None

def query_tts_api(text):
    try:
        response = requests.post(API_URL_TTS, headers=headers, json={"inputs": text})
        return response.content  # Binary audio data
    except Exception as e:
        st.error(f"Failed to call TTS API: {str(e)}")
        return None

def main():
    st.title("YouTube Caption, Summarizer, and TTS")
    url = st.text_input("Enter YouTube video URL", "")

    if st.button("Fetch Video Info"):
        if url:
            video_id, thumbnail_url = fetch_video_info(url)
            if video_id:
                display_thumbnail(thumbnail_url)
                captions, lang_code = fetch_captions(video_id)
                if captions:
                    st.text_area("Captions", captions, height=300)
                    if st.button("Summarize Captions"):
                        output = query_summarization_api(captions, 50, 200)
                        if output and 'summary_text' in output:
                            st.text_area("Summary", output['summary_text'], height=200)
                            if st.button("Generate Audio for Summary"):
                                audio_data = query_tts_api(output['summary_text'])
                                if audio_data:
                                    audio_file_path = "summary_audio.wav"
                                    with open(audio_file_path, "wb") as f:
                                        f.write(audio_data)
                                    st.audio(audio_file_path)
                                    st.download_button("Download Audio", audio_data, file_name="summary_audio.wav", mime="audio/wav")
                                else:
                                    st.error("Failed to generate audio.")
                        else:
                            st.error("Failed to summarize captions.")
                else:
                    st.error("Unable to fetch captions for this video.")
            else:
                st.error("Failed to fetch video data. Check the provided URL.")

if __name__ == "__main__":
    main()
