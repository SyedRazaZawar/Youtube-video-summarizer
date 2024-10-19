import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
from gtts import gTTS
import os

# Initialize Streamlit app layout
st.title('YouTube Video Transcript Summarizer and Audio Converter')

# Input field for YouTube video URL
video_url = st.text_input('Enter YouTube video URL:', '')

def get_video_id(url):
    """Extract video ID from YouTube URL."""
    if "youtube.com" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be" in url:
        return url.split("/")[-1]
    return None

def fetch_transcript(video_id):
    """Fetch transcript for a given YouTube video ID."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = ' '.join([text['text'] for text in transcript])
        return full_text
    except Exception as e:
        return str(e)

def summarize_text(text):
    """Generate a summary of the provided text."""
    summarizer = pipeline("summarization")
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
    return summary[0]['summary_text']

def text_to_audio(text):
    """Convert text to speech."""
    tts = gTTS(text=text, lang='en')
    audio_file = 'summary_audio.mp3'
