from urllib.parse import unquote_plus
from secrets import token_urlsafe
from flask import Flask, render_template, request, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, or_
from minio import Minio
from minio.policy import Policy
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)

app = Flask(__name__)
app.config.from_envvar('MEMEARCHIVE_SETTINGS')

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
        return '{}/memes/{}'.format(app.config['MINIO_URL'], self.id)

    # returns a link to the meme page for this meme
    def get_page(self):
        return '/meme/{}'.format(self.id)


# Minio configuration
minioClient = Minio(app.config['MINIO_URL'].split('/')[2],
                    access_key=app.config['MINIO_ACCESS_KEY'],
                    secret_key=app.config['MINIO_SECRET_KEY'],
                    secure='https://' in app.config['MINIO_URL'])

# Allowed image file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# does a file have the correct extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# TODO: this is really basic CSRF that uses sessions, when adding accounts this should be replaced
@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(400)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = token_urlsafe(16)
    return session['_csrf_token']


app.jinja_env.globals['csrf_token'] = generate_csrf_token


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


@app.route('/search/<string:quoted_query>')
def search(quoted_query: str):
    query = unquote_plus(quoted_query)
    # note that for postgresql search, you cannot have spaces in your query
    # you must use either & for and or | for or
    # https://stackoverflow.com/questions/16465466/postgres-search-query-error-if-space-used
    results = Meme.query.filter(or_(Meme.name.match(query.replace(' ', '|')),
                                    Meme.transcription.match(query.replace(' ', '|')))).all()
    return render_template('search.html', results=results, query=query)


# render the search page on the search route when nothing is entered
@app.route('/search/')
def search_nothing():
    return render_template('search.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/meme/<int:meme_id>')
def meme(meme_id: int):
    if not meme_id:
        return render_template('meme.html', invalid=True)

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
