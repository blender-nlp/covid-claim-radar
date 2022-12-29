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

COPY ./environment.yml /
RUN /opt/conda/bin/conda env create -f environment.yml
RUN /opt/conda/bin/conda init bash 
SHELL ["conda", "run", "-n", "genie", "/bin/bash", "-c"]
# RUN /opt/conda/bin/conda activate genie 
RUN /opt/conda/bin/conda clean -tipsy


COPY ./models /models
COPY ./genie /genie 
COPY ./test_cs.py /
COPY ./event_role_KAIROS_P2.json /
COPY ./app.py /

LABEL maintainer="zoey.lee13@gmail.com"

CMD ["/bin/bash"]