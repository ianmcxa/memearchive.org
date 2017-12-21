from flask import Flask, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
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

    # returns a direct link to the image
    def get_url(self):
        return '{}/memes/{}'.format(MINO_URL, self.id)

    # returns a link to the meme page for this meme
    def get_page(self):
        return '/meme/{}'.format(self.id)


### MINIO CONFIGURATION ###
MINO_URL = 'http://localhost:9000'
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
    # get the latest 8 memes
    latest_memes = Meme.query.order_by(desc(Meme.id)).limit(8)
    return render_template('index.html', latest_memes=latest_memes)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/meme/<meme_id>')
def meme(meme_id):
    if not meme_id:
        return render_template('meme.html', invalid=True)

    meme_id = int(meme_id)

    meme = Meme.query.filter_by(id=meme_id).first()
    return render_template('meme.html', meme=meme)


def minio_upload(file, name: str) -> bool:
    file.seek(0, 2)
    size = file.tell()
    file.seek(0, 0)
    try:
        minioClient.put_object('memes', name, file, size)
        return True
    except ResponseError or TypeError as err:
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
        if not file or not allowed_file(file.filename):
            return render_template('upload.html', failed=True, error_message='Invalid file type')

        # get the metadata from the submitted form
        original = 'original' in request.form

        meme = Meme(name=request.form['name'],
                    transcription=request.form['transcription'],
                    source_url=request.form['src-url'],
                    original=original,
                    upload_ip=request.remote_addr)

        db.session.add(meme)
        db.session.commit()
        image_saved = minio_upload(file, str(meme.id))
        if image_saved:
            return render_template('upload.html', success=True, meme_link='/meme/{}'.format(meme.id))
        else:
            db.session.delete(meme)
            db.session.commit()
            return render_template('upload.html', failed=True, error_message='Could not upload to image storage')

    return render_template('upload.html')
