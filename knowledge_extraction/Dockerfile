FROM ubuntu:latest

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 LANGUAGE=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

ENV PATH /usr/local/nvidia/bin/:$PATH
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64
# Tell nvidia-docker the driver spec that we need as well as to
# use all available devices, which are mounted at /usr/local/nvidia.
# The LABEL supports an older version of nvidia-docker, the env
# variables a newer one.
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility
LABEL com.nvidia.volumes.needed="nvidia_driver"
ARG DEBIAN_FRONTEND=noninteractive

# Install base packages.
RUN apt-get update --fix-missing && apt-get install -y \
    bzip2 \
    ca-certificates \
    gcc \
    git \
    libc-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    wget \
    unzip \
    libhdf5-dev \
    libevent-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc

# event argument: genie
COPY ./gen_arg gen_arg
RUN /opt/conda/bin/conda env create -f gen_arg/environment.yml
# RUN /opt/conda/bin/conda activate genie 
RUN /opt/conda/bin/conda clean -tipsy

# aida_tmp
ADD ./EventTimeArg /EventTimeArg
RUN /opt/conda/bin/conda create -n aida_tmp python=3.7
# RUN /opt/conda/envs/aida_tmp/bin/pip install -r ./EventTimeArg/aida-tmp-requirements.txt
RUN /opt/conda/envs/aida_tmp/bin/pip install numpy==1.18.5 configargparse==1.2.3 tqdm lxml==4.5.2
# RUN /opt/conda/envs/aida_tmp/bin/pip install dgl-cu110 dglgo -f https://data.dgl.ai/wheels/repo.html
# pytorch-1.5.1-py3.7_cuda10.2.89_cudnn7.6.5_0
RUN /opt/conda/bin/conda install --name aida_tmp pytorch=1.8 cudatoolkit=10.2 -c pytorch
# dgl-cuda10.2-0.8.1
RUN /opt/conda/bin/conda install --name aida_tmp -c dglteam dgl-cuda10.2=0.8 -y
# transformers-3.0.2-py3-none-any.whl
RUN /opt/conda/envs/aida_tmp/bin/pip install transformers==3.0.2
RUN /opt/conda/envs/aida_tmp/bin/pip install langdetect jieba nltk
RUN /opt/conda/envs/aida_tmp/bin/python -m nltk.downloader popular -d /opt/conda/envs/aida_tmp/share/nltk_data

# preprocessing using py36
ADD ./postprocessing /postprocessing
RUN cd /postprocessing/AIDA-Interchange-Format-master.m54/python && \
    /opt/conda/envs/genie/bin/python setup.py install

ADD ./preprocessing /preprocessing

ADD ./typing /typing

# LABEL maintainer="hengji@illinois.edu"

CMD ["/bin/bash"]

# docker build -t blendernlp/covid-claim-radar:ke .