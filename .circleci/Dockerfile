FROM girder/girder_test:latest-py2

USER root

RUN npm install --global yarn \
  && apt-get update \
  && apt-get install --assume-yes \
    # Install Pillow dependencies
    # https://pillow.readthedocs.org/en/latest/installation.html)
    libtiff5-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.5-dev \
    tk8.5-dev \
    python-tk \
    # Install isic_archive dependencies
    p7zip-full \
    # Install testing dependencies
    python3-pip \
  && pip3 install tox

USER circleci
