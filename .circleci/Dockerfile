FROM circleci/python:3.6-node

USER root

RUN apt-get update \
  && apt-get install --assume-yes \
    # Install isic_archive dependencies
    p7zip-full \
  && rm --recursive --force /var/lib/apt/lists/*

RUN pip3 --no-cache-dir install tox

USER circleci
