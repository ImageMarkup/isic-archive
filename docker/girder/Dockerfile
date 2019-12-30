FROM python:3.6.8

USER root

RUN apt-get update && apt-get install --assume-yes curl

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
  p7zip-full netcat

VOLUME /assetstore

ENV PYTHONPATH=/isic
COPY docker/requirements.txt /isic/requirements.txt
RUN pip install numpy
RUN pip install -r /isic/requirements.txt
COPY . /isic
RUN cd /usr/local/lib/python3.6/site-packages && python /isic/setup.py develop

RUN girder build --dev

ADD docker/girder/.env /root/.girder/.env
ADD docker/girder/bootstrap-isic.py /bootstrap-isic.py

ARG entrypoint
ADD $entrypoint ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
