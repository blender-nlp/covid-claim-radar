FROM ubuntu:latest

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

RUN apt update && \
    apt upgrade -y && \
    apt install wget -y &&\
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

# only needs to change this part to your own environment requirement
RUN /opt/conda/bin/conda update -n base -c defaults conda && \
    /opt/conda/bin/conda install pytorch torchvision torchaudio cudatoolkit=10.2 -c pytorch && \
    /opt/conda/bin/conda install pip spacy && \
    /opt/conda/bin/pip install transformers==4.14.1 && \
    /opt/conda/bin/pip install flask && \
    /opt/conda/bin/pip install flask-cors flask_bootstrap flask_moment flask_wtf && \
    /opt/conda/bin/pip install tornado && \
    /opt/conda/bin/pip install nltk && \
    /opt/conda/bin/pip install tqdm && \
    /opt/conda/bin/pip install scipy==1.6.2 && \
    /opt/conda/bin/pip install scikit-learn && \
    /opt/conda/bin/python -m spacy download en_core_web_sm

COPY keywords.json /keywords.json
COPY qnode_map.json /qnode_map.json
COPY process.py /process.py
