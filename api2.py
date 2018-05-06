from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_restplus import Api, Resource, fields
from sqlalchemy import create_engine
from sqlalchemy.orm import *
from json import dumps
import os
import subprocess
from pathlib import Path
import random
import mutagen
import time
from mutagen.flac import FLAC, Picture
import contextlib

'''This programs depend on view_t9 and view_t10 on hifitrack database'''

app = Flask(__name__)
e = create_engine('mysql+pymysql://root:ilovehifi@localhost/hifitrackD72?charset=utf8', pool_size=80, max_overflow=20, pool_timeout=5)

api = Api(app, version='1.0', title='Hifitrack API',
    description='Admin API',
)
ns = api.namespace('api', description='HifiTrack operations')

song_table_model = api.model("data", {
    'order_id': fields.Integer(readOnly=True, description='The order id unique identifier'),
    'product_id': fields.Integer(readOnly=True, description='The product unique identifier'),
    'product_name': fields.String(required=True, description='The product name'),
    'language': fields.String(required=True, description='Language')
})

#Connect to databse

@ns.route('/cart/add/<int:order_id>/<int:product_id>/<language>/<type>')
class cart_add(Resource):
    def handle_song(self, internal_id, order_id, language, type, is_bundle):

        conn = e.connect()
        query = "select * from view_t9 where product_id= %s and language= %s"
        query = conn.execute(query, internal_id, language)
        order_id = order_id
        result_set = query.fetchall()

        for row in result_set:
            ''' for testing only, hardcode to handle flac '''
            if type=="flac":
                ext = "flac"
            else:
                ext = row["extension"]

            filename = row["track_no"] + "_" + row["song_title"] +  "_" + row["artist_title"] +  "_" + row["album_title"] \
             +  "_" + row["format_name"] + '.' + ext
            for c in r'[]/\;,><&*:%=+@!#^()|?^':
                filename = filename.replace(c,'')
            for d in r'[]/\;,><&*:%=+@!#^()|?^':
                bundle_dir_name = row["album_title"].replace(d,'')
            product_id = internal_id
            #source_path = row["field_nextcloud_url_value"]
            source_path = "./1234/1/Track01.wav"
            albumart = './1234/1/file5.jpg' # should get from hifitrack album_art

            if is_bundle:
                output_dir = Path(".")/f"{order_id}"/f"{bundle_dir_name}"
            else:
                output_dir = Path(".")/f"{order_id}"

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            output_file = os.path.join(output_dir, filename)
        
        
        if type=="flac":
            flac_path, file_extension = os.path.splitext(source_path)
            flac_directory, wav_file_name = os.path.split(source_path)
            wav_file_name_only, wav_file_ext_only = wav_file_name.split(".")
            wav_file_name_only = wav_file_name_only + str(random.randint(1,1001))  # deal with multiple version of song working on the same temp file
            flac_source_path = flac_path + ".flac"
            if os.path.isfile(flac_source_path) != 1:
                p1 = subprocess.Popen(['flac', source_path],stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
            else:
                p1 = subprocess.Popen(["ls"],stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
            #insert metadata by metaflac
            #this part run synchronously using pipe to make sure they run in sequence
            flac_target = os.path.join(output_dir, wav_file_name_only + ".flac" )    
            
            p2 = subprocess.Popen(['cp', flac_source_path , flac_target], stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  
            p1.stdout.close()  
          
            #out, err = p5.communicate()  
            end_of_pipe, err = p2.communicate()
            p2.stdout.close()

            while not os.path.exists(flac_target):
                time.sleep(1)

            if os.path.isfile(flac_target):
                
                audio = FLAC(flac_target)
                image = Picture()
                image.type = 3
                mime = 'image/jpeg'
                image.desc = 'front cover'
                with open(albumart, 'rb') as f: 
                    image.data = f.read()
                audio.add_picture(image)
                audio["title"] = row["song_title"] 
                audio["album"] = row["album_title"] 
                audio["tracknumber"] = row["track_no"]
                audio["artist"] = row["artist_title"] 
                audio.save()
                os.rename(flac_target,output_file)
             
        else:    
            subprocess.Popen(['cp', source_path , output_file])


    @ns.response(404, 'Not found')
    def get(self, order_id, product_id, language, type):
       
        conn = e.connect()

        query1 = "select product_id from view_t10 where bundle_id = %s and language= %s"
        query1 = conn.execute(query1, product_id, language)
        
        if query1.rowcount > 0:
            ''' handle album purchase'''
            bundle_result_set = query1.fetchall()
            for row in bundle_result_set:
                result = self.handle_song(row["product_id"], order_id, language, type, 1)
        else:
            '''song purchase'''
            result = self.handle_song(product_id, order_id, language, type, 0)
    
        conn.close()
        return result

@ns.route('/')
@ns.doc('list_all_products - 5 only')
class song_table(Resource):
    #@ns.marshal_list_with(song_table_model)
    def get(self):
        conn = e.connect()
        '''List all tasks'''
        #Perform query and return JSON data
        query = conn.execute("select * from view_t9 limit 5")
        result = {'data': [dict(zip(tuple (query.keys()) ,i)) for i in query.cursor]}
        conn.close()
        return result


@ns.route('/<int:product_id>/<language>')
@ns.doc('get_products')
class song_get_products(Resource):
   
    @ns.response(404, 'Product not found')
    @ns.param('product_id', 'The product identifier')
    #@ns.expect(song_table_model)
    def get(self, product_id, language):
        conn = e.connect()
        #Perform query and return JSON data
        query = "select * from view_t9 where product_id= %s and language= %s"
        query = conn.execute(query,product_id,language)
        result = {'data': [dict(zip(tuple (query.keys()) ,i)) for i in query.cursor]}
        conn.close()
        return result

@ns.route('/cart/remove/<int:order_id>/<int:product_id>/<type>')
@ns.doc('remove_products')
class song_remove_products(Resource):

   def song_removal(self, internal_id, order_id, type, is_bundle):

        conn = e.connect()
        query = "select * from view_t9 where product_id= %s"
        query = conn.execute(query, internal_id)
        order_id = order_id
        result_set = query.fetchall()

        for row in result_set:
            ''' for testing only, hardcode to handle flac '''
            if type=="flac":
                ext = "flac"
            else:
                ext = row["extension"]

            filename = row["track_no"] + "_" + row["song_title"] +  "_" + row["artist_title"] +  "_" + row["album_title"] \
             +  "_" + row["format_name"] + '.' + ext
            for c in r'[]/\;,><&*:%=+@!#^()|?^':
                filename = filename.replace(c,'')
            for d in r'[]/\;,><&*:%=+@!#^()|?^':
                bundle_dir_name = row["album_title"].replace(d,'')
            product_id = internal_id
            #source_path = row["field_nextcloud_url_value"]
        
            if is_bundle:
                output_dir = Path(".")/f"{order_id}"/f"{bundle_dir_name}"
            else:
                output_dir = Path(".")/f"{order_id}"

            output_file = os.path.join(output_dir, filename)
            with contextlib.suppress(FileNotFoundError):
                os.remove(output_file)
            '''if directory is empty, remove it'''
            with contextlib.suppress(FileNotFoundError):
                if os.listdir(output_dir) == [] and is_bundle:
                    os.rmdir(output_dir)

   def delete(self, order_id, product_id, type):
        conn = e.connect()

        query1 = "select product_id from view_t10 where bundle_id = %s"
        query1 = conn.execute(query1, product_id)
        
        if query1.rowcount > 0:
            ''' handle album removal'''
            bundle_result_set = query1.fetchall()
            for row in bundle_result_set:
                result = self.song_removal(row["product_id"], order_id, type, 1)
        else:
            '''song removal'''
            result = self.song_removal(product_id, order_id, type, 0)
    
        conn.close()
        return result

if __name__ == '__main__':
    app.run(debug=True)