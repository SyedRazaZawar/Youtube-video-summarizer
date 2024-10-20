import streamlit as st
from pytube import YouTube
from PIL import Image
import requests
from io import BytesIO
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.formatters import SRTFormatter
import time  # To add a delay between retries

# API URLs and headers for Hugging Face
API_URL_SUMMARIZATION = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
API_URL_TTS = "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_vits"
headers = {"Authorization": "Bearer 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"}  # Replace with your actual Hugging Face API Key

# Function to fetch video info and thumbnail
def fetch_video_info(url):
    try:
        yt = YouTube(url)
        video_id = yt.video_id
        thumbnail_url = yt.thumbnail_url
        return video_id, thumbnail_url
    except Exception as e:
        st.error("Error fetching video info: " + str(e))
        return None, None

# Function to fetch alternative thumbnails
def try_alternative_thumbnail(video_id):
    alt_urls = [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",  
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",      
        f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",      
        f"https://img.youtube.com/vi/{video_id}/sddefault.jpg",      
        f"https://img.youtube.com/vi/{video_id}/default.jpg"         
    ]
    for url in alt_urls:
        response = requests.get(url)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    return None

# Function to display the thumbnail
def display_thumbnail(url, video_id):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            st.image(image, caption="Video Thumbnail", use_column_width=True)
        else:
            st.warning(f"Default thumbnail not found. Status code: {response.status_code}. Trying alternatives...")
            alt_image = try_alternative_thumbnail(video_id)
            if alt_image:
                st.image(alt_image, caption="Alternative Video Thumbnail", use_column_width=True)
            else:
                st.error("No valid thumbnail found.")
    except Exception as e:
        st.error("Failed to display thumbnail: " + str(e))

# Function to fetch available caption languages
def fetch_available_languages(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        languages = {transcript.language_code: transcript.language for transcript in transcript_list}
        return languages
    except (NoTranscriptFound, TranscriptsDisabled):
        st.warning("No transcripts available for this video.")
        return {}

# Function to fetch captions
def fetch_captions(video_id, language_code='en'):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript([language_code])
        formatter = SRTFormatter()
        srt = formatter.format_transcript(transcript.fetch())
        return srt
    except Exception as e:
        return ""  # If no captions available, return an empty string

# Function to call Hugging Face Summarization API
def query_summarization_api(text, min_length, max_length):
    response = requests.post(API_URL_SUMMARIZATION, headers=headers, json={"inputs": text, "parameters": {"min_length": min_length, "max_length": max_length}})
    return response.json()

# Function to call Hugging Face Text-to-Speech API
def query_tts_api(text):
    response = requests.post(API_URL_TTS, headers=headers, json={"inputs": text})
    return response.content  # Binary audio data

# Function to automatically fetch captions until successful
def fetch_transcripts_automatically(video_id, selected_language_code):
    retry_count = 0
    max_retries = 5  # Limit the number of retries
    wait_time = 10  # Wait time between retries in seconds

    while retry_count < max_retries:
        captions = fetch_captions(video_id, selected_language_code)
        if captions:
            return captions
        else:
            st.warning(f"Attempt {retry_count+1}: Captions not available yet. Retrying in {wait_time} seconds...")
            retry_count += 1
            time.sleep(wait_time)  # Wait for a few seconds before retrying

    st.error("Failed to fetch captions after multiple attempts.")
    return ""

# Main function to handle UI and functionality
def main():
    st.title("YouTube Caption, Summarizer, and TTS")

    # Initialize session state for captions and summary
    if 'captions' not in st.session_state:
        st.session_state['captions'] = ""
    if 'summary' not in st.session_state:
        st.session_state['summary'] = ""
    if 'video_id' not in st.session_state:
        st.session_state['video_id'] = None
    if 'available_languages' not in st.session_state:
        st.session_state['available_languages'] = {}

    # Sidebar for managing summary length
    st.sidebar.header("Summary Settings")
    min_length = st.sidebar.slider("Min Length", 10, 500, 50)
    max_length = st.sidebar.slider("Max Length", 50, 1000, 200)

    st.warning("Please enter the link of the YouTube video which has English transcripts to avoid any error. Because at this time I have learned only English. Thanks for your cooperation.") 

    # Get URL input
    url = st.text_input("Enter YouTube video URL", "")

    # Fetch Video Info Button
    if st.button("Fetch Video Info"):
        if url:
            # Fetch video information and captions
            video_id, thumbnail_url = fetch_video_info(url)
            if video_id:
                st.session_state['video_id'] = video_id
               
                # Fetch available languages
                available_languages = fetch_available_languages(video_id)
                if available_languages:
                    st.session_state['available_languages'] = available_languages
                    language_options = list(available_languages.values())
                    selected_language = st.selectbox("Select Caption Language", language_options)
                    selected_language_code = list(available_languages.keys())[language_options.index(selected_language)]

                    # Fetch and store captions in session state, try until successful
                    captions = fetch_transcripts_automatically(video_id, selected_language_code)
                    if captions:
                        st.session_state['captions'] = captions
                        st.session_state['summary'] = ""  # Reset summary when new captions are fetched
                    else:
                        st.error("Failed to fetch captions in the selected language.")
                else:
                    st.warning("No available captions for this video.")
            else:
                st.error("Failed to fetch video data. Check the provided URL.")
    
    # Display the thumbnail if the video_id is valid
    if url:
        video_id, thumbnail_url = fetch_video_info(url)
        if video_id:
            st.session_state['video_id'] = video_id
            if thumbnail_url:
                display_thumbnail(thumbnail_url, video_id)
            else:
                st.warning("No thumbnail available for this video.")
    
    # Display captions if already fetched
    if st.session_state['captions']:
        st.text_area("Captions", st.session_state['captions'], height=300, key="captions_area_display")

        # Summarize Captions Button
        if st.button("Summarize Captions"):
            with st.spinner('Summarizing...'):
                output = query_summarization_api(st.session_state['captions'], min_length, max_length)
                if isinstance(output, list) and len(output) > 0 and 'summary_text' in output[0]:
                    st.session_state['summary'] = output[0]['summary_text']
                elif 'error' in output:
                    st.error(f"API Error: {output['error']}")
                else:
                    st.error("Unexpected response format. Please try again later.")
    
    # Display summary if available
    if st.session_state['summary']:
        st.subheader("Summary:")
        st.text_area("Summary", st.session_state['summary'], height=200, key="summary_area")

        # Text-to-Speech Button
        if st.button("Generate Audio for Summary"):
            with st.spinner('Generating audio...'):
                audio_data = query_tts_api(st.session_state['summary'])
                if audio_data:
                    st.success("Audio generated successfully!")

                    # Save audio file
                    audio_file_path = "output.wav"
                    with open(audio_file_path, "wb") as f:
                        f.write(audio_data)

                    # Play the audio
                    st.audio(audio_file_path)

                    # Download button for audio
                    st.download_button(label="Download Audio", data=audio_data, file_name="summary_audio.wav", mime="audio/wav")
                else:
                    st.error("Failed to generate audio.")

if __name__ == "__main__":
    main()  
