import os
import subprocess
from flask import Flask, request, g

app = Flask(__name__)

flac_target = './1234/1/Track01.flac'
args4 = '--import-picture-from=' + './1234/1/file2.jpg'
args3 = '--set-tag=ARTIST=Lindsay3'

@app.route('/')
def generate():
    #p3 = subprocess.Popen(['metaflac' , args4, flac_target]) 
    subprocess.Popen(['metaflac' , args4, flac_target]) 
    return "done"
            