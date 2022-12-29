FROM nvidia/cuda:10.2-base-ubuntu16.04
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH
# Install base packages.
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Chicago
RUN apt-get update --fix-missing && apt-get install -y tzdata && apt-get install -y bzip2 ca-certificates curl gcc git libc-dev libglib2.0-0 libsm6 libxext6 libxrender1 wget libevent-dev build-essential &&  rm -rf /var/lib/apt/lists/*
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py37_4.12.0-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc
RUN /opt/conda/bin/conda update -n base -c defaults conda && \
    /opt/conda/bin/conda install pip && \
    /opt/conda/bin/pip install torch==1.8.0 && \
    /opt/conda/bin/pip install tqdm && \
    /opt/conda/bin/pip install transformers && \
    /opt/conda/bin/pip install flask && \
    /opt/conda/bin/pip install flask-cors && \
    /opt/conda/bin/pip install tornado && \
    /opt/conda/bin/pip install nltk && \
    /opt/conda/bin/pip install cffi && \
    /opt/conda/bin/pip install numpy && \
    /opt/conda/bin/pip install regex && \
    /opt/conda/bin/pip install sacrebleu && \
    /opt/conda/bin/pip install ipdb && \
    /opt/conda/bin/pip install spacy && \
    /opt/conda/bin/pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.2.5/en_core_web_sm-2.2.5.tar.gz && \
    /opt/conda/bin/pip install omegaconf && \
    /opt/conda/bin/pip install hydra-core && \
    /opt/conda/bin/pip install h5py && \
    /opt/conda/bin/python -m spacy download en
ADD ./args_extractor /args_extractor
ADD ./.cache /root/.cache
WORKDIR /args_extractor/transition-amr-parser-master 
RUN /opt/conda/bin/pip install --no-deps --editable fairseq-stack-transformer-v0.3.3
RUN /opt/conda/bin/pip install --editable . 

LABEL maintainer="zixuan11@illinois.edu"
WORKDIR /args_extractor
CMD ["/bin/bash"]
