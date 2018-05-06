import os.path
import time
import mutagen
from mutagen.flac import FLAC, Picture

file_path="./1234/1/Track01.flac"
albumart="./1234/1/file4.jpg"

while not os.path.exists(file_path):
    time.sleep(1)

if os.path.isfile(file_path):
    
    audio = FLAC(file_path)
    image = Picture()
    image.type = 3
    if albumart.endswith('png'):
        mime = 'image/png'
    else:
        mime = 'image/jpeg'
    image.desc = 'front cover'
    with open(albumart, 'rb') as f: # better than open(albumart, 'rb').read() ?
        image.data = f.read()

    audio.add_picture(image)
    audio["title"] = "Title 2"
    audio["album"] = "Album name"
    audio["artist"] = "PYjin"
    audio.save()

