FROM umrds/serval_core_worker-gui:0.2.3.b8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    imagemagick \
    unzip \
    python3-numpy \
    gdb \
    cmake \
    && rm -rf /var/lib/apt/lists/*

RUN pip install numpy dlib Pillow

COPY shared/ /shared
COPY shared/dotcore/myservices/dtnrpc.py /root/.core/myservices/dtnrpc.py
COPY shared/dotcore/myservices/logger.py /root/.core/myservices/logger.py

RUN echo "export PATH=/shared/dtnrpc:$PATH" >> /root/.bashrc
