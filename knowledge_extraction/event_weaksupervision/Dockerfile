FROM nvidia/cuda:10.2-base-ubuntu16.04
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH
# Install base packages.
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Chicago
RUN apt-get update --fix-missing && apt-get install -y tzdata && apt-get install -y bzip2 ca-certificates curl gcc git libc-dev libglib2.0-0 libsm6 libxext6 libxrender1 wget libevent-dev build-essential &&  rm -rf /var/lib/apt/lists/*
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc
RUN /opt/conda/bin/conda update -n base -c defaults conda
RUN /opt/conda/bin/conda install pytorch torchvision torchaudio cudatoolkit=10.2 -c pytorch
RUN /opt/conda/bin/conda install -c huggingface transformers==4.11.3
RUN /opt/conda/bin/conda install numpy==1.19.2
RUN /opt/conda/bin/conda install tqdm==4.62.2 
RUN /opt/conda/bin/conda install lxml==4.6.3
RUN /opt/conda/bin/conda install pip==21.2.4
RUN /opt/conda/bin/conda install flask==2.0.1
RUN /opt/conda/bin/pip install nltk
RUN /opt/conda/bin/conda clean -tipsy
ADD ./event_weaksupervision/ /event_weaksupervision
WORKDIR /event_weaksupervision
LABEL maintainer="hengji@illinois.edu"
