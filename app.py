import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
from gtts import gTTS
import os

# Set up the title of the Streamlit app
st.title('YouTube Video Transcript Summarizer and Audio Converter')

# User input for YouTube video URL
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
    tts.save(audio_file)
    return audio_file

if st.button('Fetch Transcript'):
    video_id = get_video_id(video_url)
    if video_id:
        transcript = fetch_transcript(video_id)
        if transcript:
            st.text_area("Transcript", transcript, height=250)
            # The button to summarize is displayed only if there is no summary in session state
            if 'summary' not in st.session_state:
                if st.button('Summarize Transcript'):
                    st.session_state['summary'] = summarize_text(transcript)
            if 'summary' in st.session_state:
                st.text_area("Summary", st.session_state['summary'], height=150)
                if st.button('Convert Summary to Audio'):
                    audio_file = text_to_audio(st.session_state['summary'])
                    st.audio(audio_file)
                    with open(audio_file, "rb") as file:
                        st.download_button(
                            label="Download Summary Audio",
                            data=file,
                            file_name=audio_file,
                            mime='audio/mp3'
                        )

# Creating a directory to store audio files, if it doesn't exist
if not os.path.exists('audio'):
    os.makedirs('audio')
