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

# event argument
COPY ./gen_arg gen_arg
RUN /opt/conda/bin/conda env create -f gen_arg/environment.yml
# RUN /opt/conda/bin/conda activate genie 
RUN /opt/conda/bin/conda clean -tipsy

# preprocessing using py36
ADD ./postprocessing /postprocessing
RUN cd /postprocessing/AIDA-Interchange-Format-master.m54/python && \
    /opt/conda/envs/py36/bin/python setup.py install

RUN /opt/conda/bin/conda clean -tipsy

ADD ./preprocessing /preprocessing

# LABEL maintainer="hengji@illinois.edu"

CMD ["/bin/bash"]

# docker build -t blendernlp/covid-claim-radar:ke .