from flask import Flask, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from minio import Minio
from minio.policy import Policy
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)

app = Flask(__name__)
app.secret_key = '05eb2517-ccfa-4393-a1e9-4cefcb19a2a1'

### DATABASE CONFIGURATION ###
# TODO: use postgres for any real usage
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///memearchive.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Meme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.Text)
    transcription = db.Column(db.Text, nullable=False)
    original = db.Column(db.Boolean)
    upload_ip = db.Column(db.String(128), nullable=False)


### MINIO CONFIGURATION ###
minioClient = Minio('localhost:9000',
                    access_key='9VAVA93ASWI3IJROBS2W',
                    secret_key='BsBJfwNGmrVWqBDooo1QozlEMtmuDceEGni0eu/C',
                    secure=False)

# Allowed image file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.cli.command('setup')
def setup():
    app.logger.debug('running setup')
    # setup minio
    try:
        minioClient.make_bucket('memes')
        app.logger.debug('Created minio bucket memes')
    except BucketAlreadyOwnedByYou as err:
        app.logger.debug('bucket memes already exists')
        pass
    except BucketAlreadyExists as err:
        app.logger.debug('bucket memes already exists')
        pass
    except ResponseError as err:
        app.logger.debug('Could not connect to minio, is it running?')
        raise

    try:
        minioClient.set_bucket_policy('memes', '', Policy.READ_ONLY)
    except ResponseError as err:
        app.logger.debug('Could not connect to minio, is it running?')
        raise

    # setup database
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


def minio_upload(file, name) -> bool:
    file.seek(0, 2)
    size = file.tell()
    file.seek(0, 0)
    try:
        minioClient.put_object('memes', name, file, size)
        return True
    except ResponseError as err:
        app.logger.error('Could not upload file, is minio running?\n{}'.format(err))
        return False

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return render_template('upload.html', failed=True, error_message='No file uploaded')
        file = request.files['file']
        # if we get an empty filename
        if file.filename == '':
            return render_template('upload.html', failed=True, error_message='Cannot upload blank file')
        if file and allowed_file(file.filename):
            # get the metadata from the submitted form
            name = request.form['name']
            transcription = request.form['transcription']
            source_url = request.form['src-url']
            original = request.form['original']
            upload_ip = request.remote_addr

            image_saved = minio_upload(file, name)
            if image_saved:
                meme = Meme(name=name, transcription=transcription,
                            source_url=source_url, original=original,
                            upload_ip=upload_ip)

                db.session.add(meme)
                db.session.commit()
                return render_template('upload.html', success=True)

        return render_template('upload.html', failed=True, error_message='Invalid file type')

    return render_template('upload.html')
