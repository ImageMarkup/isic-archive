FROM circleci/python:3.6

USER root

RUN apt-get update && \
    apt-get install --assume-yes curl

RUN curl --silent --location https://deb.nodesource.com/setup_10.x | bash - \
  && apt-get install --assume-yes nodejs \
  && npm install --global npm

RUN npm install --global yarn \
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
    libvips-tools \
    # Install isic_archive dependencies
    p7zip-full \
  && pip3 install tox

RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash \
    && apt-get install git-lfs

USER circleci
