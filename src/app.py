from flask import Flask, render_template, request, flash, redirect
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from minio import Minio
from minio.error import ResponseError

app = Flask(__name__)

### DATABASE CONFIGURATION ###
# TODO: use postgres for any real usage
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///memearchive.db'
db = SQLAlchemy(app)

### MINIO CONFIGURATION ###
minioClient = Minio('localhost:9000',
                    access_key='Q3AM3UQ867SPQQA43P2F',
                    secret_key='zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG',
                    secure=False)

# Allowed image file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

    return render_template('upload.html')

