import os
import openai
from time import time,sleep
import textwrap
import re
import glob2
from pytube import YouTube
from pydub import AudioSegment
import requests

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

openai.api_key = open_file('openaiapikey.txt')

chatbot5 = open_file('chatbot5.txt')

elapikey = open_file('elabapikey.txt')

conversation = []

#THIS FUNCTION USES TEXT DAVINCI 003 API TO SUMMARIZE
def gpt_3(prompt, engine='text-davinci-003', temp=0.6, top_p=1.0, tokens=1000, freq_pen=0.0, pres_pen=0.0, stop=['asdfasdf', 'asdasdf']):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
    while True:
        try:
            response = openai.Completion.create(
                engine=engine,
                prompt=prompt,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,
                stop=stop)
            text = response['choices'][0]['text'].strip()
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(1)
            
def chatgpt3(userinput, temperature=0.6, frequency_penalty=0, presence_penalty=0):
    max_retry = 6
    retry = 0
    messagein = [
        {"role": "user", "content": userinput },
        {"role": "system", "content": chatbot5}]
    while True:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                temperature=temperature,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                messages=messagein
            )
            text = response['choices'][0]['message']['content']
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(1)          


# paste the YouTube video link here
video_url = open_file("URL.txt")

# create a YouTube object
youtube = YouTube(video_url)

# get the highest resolution video stream
video_stream = youtube.streams.get_highest_resolution()

#Your Pathfolder
pathfolder = 'C:/Users/kris_/Python/Podcast-sum'
   
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
        print(transcript)
        transcripts.append(transcript.text)

    # concatenate the transcripts and save to a file in the same directory as the video file
    full_transcript = "\n".join(transcripts)
    save_file(os.path.join(pathfolder, "podscript.txt"), full_transcript)

if __name__ == '__main__':
    # get a list of all text files in the specified folder
    files = ["C:/Users/kris_/Python/Podcast-sum/podscript.txt"]
    
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
        prompt = open_file('prompt.txt').replace('<<SUMMARY>>', chunk)
        prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
        summary = chatgpt3(prompt)
        print('\n\n\n', count, 'out of', len(chunks), 'Compressions', ' : ', summary)
        result.append(summary)
        save_file("podsummary.txt", '\n\n'.join(result))

# Split the contents of pfdsummary.txt into chunks with a textwrap of 3000
    with open("podsummary.txt", 'r', encoding='utf-8') as infile:
        summary = infile.read()
        chunks = textwrap.wrap(summary, 5000)

    #Initialize empty lists to store the results
    result = []
    result2 = []

    #WRITE NOTES FROM CHUNKS
    for i, chunk in enumerate(chunks):
         #Read the contents of prompt2.txt
        with open("prompt2.txt", 'r', encoding='utf-8') as infile:
            prompt = infile.read()

        # Replace the placeholder in the prompt with the current chunk
        prompt = prompt.replace("<<NOTES>>", chunk)

        # Run the chunk through the gpt_3 function
        notes = chatgpt3(prompt)
        
        #WRITE A SUMMARY FROM NOTES
        keytw = open_file('prompt6.txt').replace('<<NOTES>>', chunk)
        keytw2 = chatgpt3(keytw)


        # Print the result
        print(f"\n\n\n{i+1} out of {len(chunks)} Compressions: {notes}")

         #Append the results to the lists
        result.append(notes)
        result2.append(keytw2)


    #Save the results to a file
    with open("notes.txt", 'w', encoding='utf-8') as outfile:
        outfile.write("\n\n".join(result))
        
    with open("notessum.txt", 'w', encoding='utf-8') as outfile:
        outfile.write("\n\n".join(result2))

    #SUMMARY OF NOTES
    sumnotes = open_file("notes.txt")
    

    #WRITE A SYNOPSIS
    keytw = open_file('prompt5.txt').replace('<<NOTES>>', sumnotes)
    keytw2 = chatgpt3(keytw)
    print(keytw2)
    save_file("synopsis3.txt", keytw2)
    
    #ElvenLabs Voice
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
        print('Text-to-speech conversion successful')
    else:
        print('Error:', response.text)
    
    
