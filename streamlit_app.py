import streamlit as st
import os
import openai
from time import time, sleep
import textwrap
import re
import glob2
from pytube import YouTube
from pydub import AudioSegment
import requests

st.title("Podcast Summarizer")

# Configuration
openai.api_key = st.text_input("Enter OpenAI API Key:")

elapikey = st.text_input("Enter ElvenLabs API Key:")

video_url = st.text_input("Enter YouTube video URL:")

submit_button = st.button("Summarize Podcast")

def open_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

  def chatgpt3(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].text.strip()


def main():
    if submit_button:
        if not video_url:
            st.warning("Please enter a YouTube video URL.")
            return

        # create a YouTube object
        youtube = YouTube(video_url)

        # get the highest resolution video stream
        video_stream = youtube.streams.get_highest_resolution()

        #Your Pathfolder
        pathfolder = '/tmp/'

        # download the video to the pathfolder directory with the filename ytvideo.mp4
        video_file_path = video_stream.download(output_path=pathfolder, filename='ytvideo.mp4')

        # split the audio from the video file into 10-minute segments
        segment_duration = 10 * 60 * 1000  # 10 minutes in milliseconds
        audio = AudioSegment.from_file(video_file_path, "mp4")
        num_segments = int(len(audio) / segment_duration) + 1
        for i in range(num_segments):
            segment = audio[i*segment_duration:(i+1)*segment_duration]
            segment_file_path = os.path.join(pathfolder, f"segment_{i}.mp3")
            segment.export(segment_file_path, format='mp3')

        # transcribe each segment of audio separately
        transcripts = []
        for i in range(num_segments):
            segment_path = os.path.join(pathfolder, f"segment_{i}.mp3")
            with open(segment_path, "rb") as f:
                transcript = openai.Audio.transcribe("whisper-1", f)
                transcripts.append(transcript.text)

        # concatenate the transcripts and save to a file in the same directory as the video file
        full_transcript = "\n".join(transcripts)
        with open(os.path.join(pathfolder, "podscript.txt"), 'w', encoding='utf-8') as outfile:
            outfile.write(full_transcript)

        # get a list of all text files in the specified folder
        files = [os.path.join(pathfolder, 'podscript.txt')]

        # initialize an empty string to store the contents of all the text files
        alltext = ""

        # iterate over the list of files
        for file in files:
            with open(file, 'r', encoding='utf-8') as infile:  # open the file
                alltext += infile.read()  # read the contents of the file and append it to the alltext string
        chunks = textwrap.wrap(alltext, 5000)
        result = list()
        count = 0

        #write a summary
        for chunk in chunks:
            count = count + 1
            prompt = open_file('prompt.txt').replace('<SUMMARY>', chunk)
            prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
            summary = chatgpt3(prompt)
            st.write(f"{count} out of {len(chunks)} Compressions: {summary}")
            result.append(summary)

        # Save the summary to a file
        with open("podsummary.txt", 'w', encoding='utf-8') as outfile:
            outfile.write('\n\n'.join(result))
                                      
        # Split the contents of podsummary.txt into chunks with a textwrap of 3000
        with open("podsummary.txt", 'r', encoding='utf-8') as infile:
            summary = infile.read()
            chunks = textwrap.wrap(summary, 5000)

        # Initialize empty lists to store the results
        result = []
        result2 = []

        # WRITE NOTES FROM CHUNKS
        for i, chunk in enumerate(chunks):
            # Read the contents of prompt2.txt
            with open("prompt2.txt", 'r', encoding='utf-8') as infile:
                prompt = infile.read()

            # Replace the placeholder in the prompt with the current chunk
            prompt = prompt.replace("<NOTES>", chunk)

            # Run the chunk through the gpt_3 function
            notes = chatgpt3(prompt)

            # WRITE A SUMMARY FROM NOTES
            keytw = open_file('prompt6.txt').replace('<NOTES>', chunk)
            keytw2 = chatgpt3(keytw)

            # Print the result
            st.write(f"{i+1} out of {len(chunks)} Compressions: {notes}")

            # Append the results to the lists
            result.append(notes)
            result2.append(keytw2)

        # Save the results to a file
        with open("notes.txt", 'w', encoding='utf-8') as outfile:
            outfile.write("\n\n".join(result))

        with open("notessum.txt", 'w', encoding='utf-8') as outfile:
            outfile.write("\n\n".join(result2))

        # SUMMARY OF NOTES
        sumnotes = open_file("notes.txt")

        # WRITE A SYNOPSIS
        keytw = open_file('prompt5.txt').replace('<NOTES>', sumnotes)
        keytw2 = chatgpt3(keytw)
        st.write("Synopsis:", keytw2)

        # Save the synopsis to a file
        with open("synopsis3.txt", 'w', encoding='utf-8') as outfile:
            outfile.write(keytw2)

        # ElvenLabs Voice
        url = 'https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL'
        headers = {
            'accept': 'audio/mpeg',
            'xi-api-key': elapikey,
            'Content-Type': 'application/json'
        }
        data = {
            'text': keytw2,
            'voice_settings': {
                'stability': 0.6,
                'similarity_boost': 0.85
            }
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            with open('voicesum.mp3', 'wb') as f:
                f.write(response.content)
            st.success('Text-to-speech conversion successful')
            st.audio('voicesum.mp3')
        else:
            st.error(f"Error: {response.text}")

if __name__ == "__main__":
    main()
