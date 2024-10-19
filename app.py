import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
from gtts import gTTS
import os

# Streamlit app layout
st.title('YouTube Video Transcript Summarizer and Audio Converter')

# Input for YouTube video URL
video_url = st.text_input('Enter YouTube video URL:', '')

def get_video_id(url):
    # Extracting video ID from URL
    if "youtube.com" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be" in url:
        return url.split("/")[-1]
    return None

def fetch_transcript(video_id):
    try:
        # Fetching the transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = ' '.join([text['text'] for text in transcript])
        return full_text
    except Exception as e:
        return str(e)

def summarize_text(text):
    # Load summarization model
    summarizer = pipeline("summarization")
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
    return summary[0]['summary_text']

def text_to_audio(text):
    tts = gTTS(text=text, lang='en')
    audio_file = 'audio/summary_audio.mp3'
    tts.save(audio_file)
    return audio_file

video_id = None
if video_url:
    video_id = get_video_id(video_url)

if video_id:
    if st.button('Fetch Transcript'):
        transcript = fetch_transcript(video_id)
        st.session_state['transcript'] = transcript  # Store transcript in session state

if 'transcript' in st.session_state:
    st.text_area("Transcript", st.session_state['transcript'], height=250)

    if st.button('Summarize Transcript'):
        summary = summarize_text(st.session_state['transcript'])
        st.session_state['summary'] = summary  # Store summary in session state

if 'summary' in st.session_state:
    st.text_area("Summary", st.session_state['summary'], height=150)

    if st.button('Convert Summary to Audio'):
        audio_file = text_to_audio(st.session_state['summary'])
        st.audio(audio_file)
        with open(audio_file, "rb") as file:
            st.download_button(
                label="Download Summary Audio",
                data=file,
                file_name='summary_audio.mp3',
                mime='audio/mp3'
            )

# Ensure local assets directory exists for saving audio files
if not os.path.exists('audio'):
    os.makedirs('audio')
