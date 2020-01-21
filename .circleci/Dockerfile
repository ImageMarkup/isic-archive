FROM circleci/python:3.6-node

USER root

RUN apt-get update \
  && apt-get install --assume-yes \
    # Install isic_archive dependencies
    p7zip-full

RUN pip3 install tox

USER circleci
