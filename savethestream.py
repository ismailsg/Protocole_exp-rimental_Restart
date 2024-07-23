

import cv2
import os
#os.add_dll_directory(r'C:\Program Files (x86)\VideoLAN\VLC')
import vlc

import urllib.request
import sounddevice as sd
import numpy as np
import threading
import zipfile
from scipy.io.wavfile import write
import moviepy.editor as mp
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import time
from scipy.io.wavfile import read




# Specify the path to libvlc.dll

def zip_folder(folder_path, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), folder_path))

    # Remove the original folder after zipping
    if os.path.exists(folder_path):
        for root, _, files in os.walk(folder_path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            os.rmdir(folder_path)
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    service_account_file = 'service_account.json'
    parent_folder = '1iZQUDMjNuI2-Nit4-6I2akd2Yvlb8j_O'

    creds = service_account.Credentials.from_service_account_file(service_account_file,scopes=SCOPES)
    service = build('drive','v3',credentials=creds)
    file_metadata = {
        'name': os.path.basename(zip_file_path),
        'parents': [parent_folder]
    }
    
    media = MediaFileUpload(zip_file_path, mimetype='application/zip')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
         
    os.remove(zip_file_path)

def record_audio(duration, audio_file_path):
    freq = 44100
    recording = sd.rec(int(duration * freq), samplerate=freq, channels=2)
    sd.wait()  # Wait until the recording is finished
    write(audio_file_path, freq, recording)

def capture_and_save_reaction(video_link, reaction_name):
    # Download the video
    urllib.request.urlretrieve(video_link, 'temp_video.mp4')
    
    # Get the duration of the video
    video_clip = mp.VideoFileClip('temp_video.mp4')
    video_duration = video_clip.duration

    # Play the video
    player = vlc.MediaPlayer('temp_video.mp4')
    player.play()

    while player.get_state() != vlc.State.Playing:
        continue

    # Prepare for video capture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Could not open video device")

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_out = cv2.VideoWriter('temp_video_output.mp4', fourcc, fps, (frame_width, frame_height))

    # Start audio capture in a separate thread
    audio_file_path = 'temp_audio_output.wav'
    audio_thread = threading.Thread(target=record_audio, args=(video_duration, audio_file_path))
    audio_thread.start()

    # Capture video frames
    start_time = cv2.getTickCount()
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        video_out.write(frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or player.get_state() == vlc.State.Ended:
            break

    # Stop capturing
    cap.release()
    video_out.release()
    player.stop()
    os.remove('temp_video.mp4')

    # Wait for audio thread to finish
    audio_thread.join()

    # Ensure the audio file exists before combining
    if not os.path.exists(audio_file_path):
        raise OSError(f"Audio file {audio_file_path} not found!")

    # Combine audio and video
    video_clip = mp.VideoFileClip('temp_video_output.mp4')
    audio_clip = mp.AudioFileClip(audio_file_path)
    final_clip = video_clip.set_audio(audio_clip)
    final_clip.write_videofile(reaction_name, codec='libx264', audio_codec='aac')
    video_duration = get_video_duration('temp_video_output.mp4')
    audio_duration = get_audio_duration('temp_audio_output.wav')

    # Clean up temporary files
    os.remove('temp_video_output.mp4')
    os.remove(audio_file_path)

# Example usage:
# capture_and_save_reaction('http://example.com/video.mp4', 'reaction_output.mp4')

    print("Durée de la vidéo :", video_duration)
    print("Durée du son :", audio_duration)


def get_video_duration(video_path):
    video_clip = mp.VideoFileClip(video_path)
    return video_clip.duration

def get_audio_duration(audio_path):
    sample_rate, audio_data = read(audio_path)
    duration_seconds = len(audio_data) / sample_rate
    return duration_seconds


def main():
    pdf_path = "/home/ismail/Documents/Instructions"
    #display_instructions(pdf_path)

    volunteer_name = input("Enter the volunteer's name: ")

    folder_name = f"{volunteer_name}_reactions"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    video_links = {
        'B1.mp4': 'https://drive.google.com/uc?id=1TBT0DC_BCdEtof8NmnBKuNmUKPnQPI3F',
        #'B2.mp4': 'https://drive.google.com/uc?id=179iqGMjs45ptOvhoxDCqLuNA1e43M_cl', 
        #'B3.mp4': 'https://drive.google.com/uc?id=18byNuzkZp4H9eOVS9TyywBkwYqHSgrfp',
        #'B4.mp4': 'https://drive.google.com/uc?id=1uSEUDNdL-Jw-aWL7rXbTcIGouL4WlCNX',
        #'C1.mp4': 'https://drive.google.com/uc?id=1910Ybq5XMQDK_IkQQjfpkXBBd8fTOJgy',
        #'E1.mp4': 'https://drive.google.com/uc?id=1BZkIeMfg3ERENIbV1JjBCscg43xMyg-l'
    }

    for video_name, video_link in video_links.items():
        reaction_name = os.path.join(folder_name, f'reaction_{video_name}')
        capture_and_save_reaction(video_link, reaction_name)
        print(f'Reaction {reaction_name} saved.')
    
    folder_path = f"{volunteer_name}_reactions"
    zip_file_path = f"{volunteer_name}_reactions.zip"



    
    #zip_folder(folder_path, zip_file_path)

if __name__ == '__main__':
    main()
