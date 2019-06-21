#!/bin/bash
set -e

celery -A isic_archive.tasks worker --concurrency 1 --loglevel info
