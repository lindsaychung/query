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

@ns.route('/cart/add/<int:order_id>/<int:product_id>/<language>')
class cart_add(Resource):
    def get(self, order_id, product_id, language):
       
        conn = e.connect()
        query = "select * from view_t9 where product_id= %s and language= %s"
        query = conn.execute(query,product_id,language)
        order_id = order_id
        result_set = query.fetchall()
        for row in result_set:
            filename = row["track_no"] + "_" + row["song_title"] +  "_" + row["artist_title"] +  "_" + row["album_title"] \
             +  "_" + row["format_name"] + '.' + row["extension"]
            for c in r'[]/\;,><&*:%=+@!#^()|?^':
                filename = filename.replace(c,'')
            product_id = product_id
            source_path = row["field_nextcloud_url_value"]
            output_dir = Path(".")/f"{order_id}"
            dircreate = output_dir.mkdir(exist_ok=True)
            output_file = output_dir.name + "/" + filename
            ## should change to real path
            # subprocess.Popen(['cp', source_path, output_file])
            subprocess.Popen(['cp', "./1234/1/Track01.wav", output_file])
        conn.close()
        return filename

@ns.route('/test/cart/add/<int:order_id>/<int:product_id>/<language>/<type>')
class cart_add(Resource):
    def handle_song(self, internal_id, order_id, language, type):

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
            product_id = internal_id
            #source_path = row["field_nextcloud_url_value"]
            source_path = "./1234/1/Track01.wav"
            output_dir = Path(".")/f"{order_id}"
            dircreate = output_dir.mkdir(exist_ok=True)


            output_file = output_dir.name + "/" + filename
        
        
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
            
            args = '--set-tag=ARTIST=' + row["artist_title"] 
            args1 = '--set-tag=ALBUM=' + row["album_title"] 
            args2 = '--set-tag=TRACKNUMBER=' + row["track_no"]
            args3 = '--set-tag=TITLE=' + row["song_title"]
            args4 = '--import-picture-from=' + './1234/1/file2.jpg'
           
            p2 = subprocess.Popen(['cp', flac_source_path , flac_target], stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  
            p1.stdout.close()  
            p3 = subprocess.Popen(['mv', flac_target, output_file], stdin=p2.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
            p2.stdout.close() 
            p4 = subprocess.Popen(['metaflac', args, args1, args2, args3, output_file], stdin=p3.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p3.stdout.close()  
            p5 = subprocess.Popen(['metaflac', args4, output_file], stdin=p4.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p4.stdout.close()  
            #out, err = p5.communicate()  
            end_of_pipe, err = p5.communicate()
            p5.stdout.close()
            y = ''
            for line in end_of_pipe:
                print (line.strip())
            
        else:    
            subprocess.Popen(['cp', source_path , output_file])


    @ns.response(404, 'Todo not found')
    def get(self, order_id, product_id, language, type):
       
        conn = e.connect()

        query1 = "select product_id from view_t10 where bundle_id = %s and language= %s"
        query1 = conn.execute(query1, product_id, language)
        
        if query1.rowcount > 0:
             bundle_result_set = query1.fetchall()
             for row in bundle_result_set:
                result = self.handle_song(row["product_id"], order_id, language, type)
        else:
            result = self.handle_song(product_id, order_id, language, type)
    
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
   
    @ns.response(404, 'Todo not found')
    @ns.param('product_id', 'The task identifier')
    #@ns.expect(song_table_model)
    def get(self, product_id, language):
        conn = e.connect()
        #Perform query and return JSON data
        query = "select * from view_t9 where product_id= %s and language= %s"
        query = conn.execute(query,product_id,language)
        result = {'data': [dict(zip(tuple (query.keys()) ,i)) for i in query.cursor]}
        conn.close()
        return result

if __name__ == '__main__':
    app.run(debug=True)