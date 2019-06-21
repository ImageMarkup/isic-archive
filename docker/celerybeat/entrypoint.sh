#!/bin/bash
set -e

celery -A isic_archive.tasks beat --loglevel info
