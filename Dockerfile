FROM docker.io/python:3.13-slim

# Install packages needed to run your application (not build deps):
RUN set -ex \
    && RUN_DEPS=" \
        libexpat1 \
        libjpeg62-turbo \
        libpcre2-posix3 \
        libpq5 \
        media-types \
        postgresql-client \
        procps \
        zlib1g \
    " \
    && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
    && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS \
    && rm -rf /var/lib/apt/lists/*

# Build dependencies which are in turn removed
RUN set -ex \
    && BUILD_DEPS=" \
        build-essential \
        curl \
        git \
        libexpat1-dev \
        libjpeg62-turbo-dev \
        libpcre2-dev \
        libpq-dev \
        zlib1g-dev \
        python3-dev \
        libgmp3-dev \
        libfreetype6-dev \
        openssh-client \
        libxml2-dev \
        libxslt-dev \
        libmagic1 \
    " \
    && apt-get update && apt-get install -y --no-install-recommends $BUILD_DEPS

# Install python venv and path, upgrade pip and install poetry
RUN python3 -m venv vp3xx
ENV VIRTUAL_ENV=/vp3xx PATH=/vp3xx/bin:$PATH
RUN pip install -U pip
#RUN pip install poetry

#ENV POETRY_NO_INTERACTION=1 \
#    POETRY_VIRTUALENVS_IN_PROJECT=1 \
#    POETRY_CACHE_DIR=/tmp/poetry_cache

# Authorize SSH Host
RUN mkdir -p /root/.ssh && ssh-keyscan github.com >> /root/.ssh/known_hosts

# create app directory and add application deps
WORKDIR /home/
COPY pyproject.toml ./
#RUN poetry install --without dev --no-root

# Copy the app layers separately to speed build
# TODO can this be combined into 1 step that executes if dir has changed
COPY nada ./nada
#RUN --mount=type=ssh pip install .
RUN pip install -e .

# Remove the build deps
#RUN rm -rf $POETRY_CACHE_DIR
RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false $BUILD_DEPS \
    && rm -rf /var/lib/apt/lists/*

# start celery
ENTRYPOINT ["celery", "-A", "nada.nada_celery.celery:app", "worker", "--pool",  "gevent", "-l", "info", "--concurrency", "100", "-Ofair", "--hostname=evt1@%%h"]
