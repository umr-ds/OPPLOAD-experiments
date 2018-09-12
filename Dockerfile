FROM umrds/serval_core_worker-gui:0.2.3.b6

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    imagemagick \
    unzip \
    tcpdump \
    python3-numpy \
    gdb \
    sysstat \
    && rm -rf /var/lib/apt/lists/*

COPY shared/ /shared

RUN echo "export PATH=/shared/dtnrpc:$PATH" >> /root/.bashrc \
    && cp /shared/dotcore/myservices/dtnrpc.py /root/.core/myservices/dtnrpc.py \
    && cp /shared/dotcore/myservices/logger.py /root/.core/myservices/logger.py \
    && sed -i 's/{DefaultRoute SSH}/{DefaultRoute SSH Serval DTN-RPyC Logger}/g' /root/.core/nodes.conf
