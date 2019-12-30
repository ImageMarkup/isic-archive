#!/bin/bash
set -e

until nc -z mongo 27017; do sleep 1; done;
girder serve --host 0.0.0.0
