# Memearchive.org

The purpose of this site is to preserve humanities memes.

## Installation

The memearchive system reads a configuration file from the
`MEMEARCHIVE_SETTINGS` environment variable. An example of this
configuration file is included in the repo.

You will need to set your secret key, postgres access and minio url
and keys.

### Dependencies

* postgresql - stores all metadata. postgres specifically required
for text search functions needed by the system.
* [minio](minio.io) - object storage API, S3 can be substituted if you
are deploying on AWS.
* Python 3 - memearchive.org uses python 3 specific features

#### Packages

All of these should be installable via pip (note you may need to use
`pip3`)

* Flask
* Flask-sqlalchemy
* sqlalchemy
* minio

Once you have the postgres and minio connections configured
you will need to setup the application by running `flask setup`
or `python -m flask setup` with the `FLASK_APP` environment
variable set to the path of `app.py`.

It is recommended to deploy memearchive.org behind an Nginx
proxy using Uwsgi to serve the python routes.