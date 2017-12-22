# Memearchive.org

The purpose of this site is to preserve humanities memes.

## Installation

The memearchive system reads a configuration file from the
`MEMEARCHIVE_SETTINGS` environment variable. An example of this
configuration file is included in the repo.

### Dependencies

* postgresql - stores all metadata. postgres specifically required
for text search functions needed by the system.
* [minio](minio.io) - object storage API, S3 can be substituted if you
are deploying on AWS.