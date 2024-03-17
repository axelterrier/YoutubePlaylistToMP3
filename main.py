import tkinter as tk
from tkinter import filedialog, simpledialog
from pytube import Playlist
import moviepy.editor as mp
import os
import eyed3
import requests
from io import BytesIO

def sanitize_filename(filename):
    """Nettoie le titre pour l'utiliser comme nom de fichier sûr."""
    valid_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(c for c in filename if c in valid_chars)

def download_image(url):
    """Télécharge l'image depuis l'URL et la retourne comme un objet BytesIO."""
    response = requests.get(url)
    image = BytesIO(response.content)
    return image

def set_mp3_tags(filename, artist, title, album_art_url):
    """Définit les métadonnées du fichier MP3, y compris la pochette d'album."""
    audiofile = eyed3.load(filename)
    if audiofile.tag is None:
        audiofile.tag = eyed3.id3.Tag()
    audiofile.tag.artist = artist
    audiofile.tag.title = title

    # Télécharge et définit la pochette d'album
    album_art = download_image(album_art_url)
    audiofile.tag.images.set(3, album_art.getvalue(), "image/jpeg")
    album_art.close()

    audiofile.tag.save(version=eyed3.id3.ID3_V2_3)

def download_playlist_as_mp3(playlist_url, output_path, update_status):
    playlist = Playlist(playlist_url)
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    total_videos = len(playlist.videos)
    current_video = 1
    
    for video in playlist.videos:
        title_split = video.title.split(" - ", 1)
        artist = title_split[0] if len(title_split) > 1 else 'Unknown Artist'
        title = title_split[1] if len(title_split) > 1 else video.title
        title = sanitize_filename(title)

        update_status(f"Téléchargement de : {artist} - {title} ({current_video}/{total_videos})")
        
        audio_stream = video.streams.get_audio_only()
        download_path = audio_stream.download(output_path=output_path, filename=title + ".mp4")

        mp4_path = download_path
        mp3_path = os.path.join(output_path, title + ".mp3")
        
        if os.path.exists(mp4_path):
            new_file = mp.AudioFileClip(mp4_path)
            new_file.write_audiofile(mp3_path)
            new_file.close()
            os.remove(mp4_path)
            
            set_mp3_tags(mp3_path, artist, title, video.thumbnail_url)
            update_status(f"Conversion terminée : {artist} - {title} ({current_video}/{total_videos})")
        else:
            update_status(f"Erreur : le fichier {mp4_path} n'a pas été trouvé.")
        
        current_video += 1

def ask_for_directory():
    """Demande à l'utilisateur de choisir un répertoire de sauvegarde."""
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title="Choisissez le dossier de destination pour les MP3")
    return folder_selected

def ask_for_playlist_url():
    """Demande à l'utilisateur de saisir l'URL de la playlist."""
    root = tk.Tk()
    root.withdraw()
    url = simpledialog.askstring("URL de la Playlist", "Entrez l'URL de la playlist YouTube:")
    return url

if __name__ == "__main__":
    output_path = ask_for_directory()
    if output_path:
        playlist_url = ask_for_playlist_url()
        if playlist_url:
            def update_status(message):
                print(message)  # Affiche le message d'état dans la console
            download_playlist_as_mp3(playlist_url, output_path, update_status)
        else:
            print("Aucune URL fournie.")
    else:
        print("Aucun dossier sélectionné.")