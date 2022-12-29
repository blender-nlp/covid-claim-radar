# FROM nvidia/cuda:10.2-runtime-ubuntu18.04
FROM nvidia/cuda:11.3.0-runtime-ubuntu20.04
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

# event argument: genie
COPY ./arg_genie /arg_genie
RUN /opt/conda/bin/conda env create -f /arg_genie/environment.yml
# RUN /opt/conda/bin/conda activate genie 
ENV PYTHONPATH "${PYTHONPATH}:/arg_genie/genie"
RUN /opt/conda/bin/conda clean -tipsy

# temporal
ADD ./EventTimeArg /EventTimeArg
RUN /opt/conda/envs/genie/bin/pip install configargparse==1.2.3
RUN /opt/conda/bin/conda install --name genie -c dglteam dgl-cuda10.2=0.5 -y
# RUN /opt/conda/bin/conda create -n aida_tmp python=3.7
# # RUN /opt/conda/envs/aida_tmp/bin/pip install -r ./EventTimeArg/aida-tmp-requirements.txt
# RUN /opt/conda/envs/aida_tmp/bin/pip install numpy==1.18.5 configargparse==1.2.3 tqdm==4.62.2 lxml==4.5.2 flask==2.0.1
# # RUN /opt/conda/envs/aida_tmp/bin/pip install dgl-cu110 dglgo -f https://data.dgl.ai/wheels/repo.html
# # pytorch-1.5.1-py3.7_cuda10.2.89_cudnn7.6.5_0
# # RUN /opt/conda/bin/conda install --name aida_tmp pytorch=1.8 cudatoolkit=11.3 -c pytorch
# # dgl-cuda10.2-0.8.1
# RUN /opt/conda/bin/conda install --name genie -c dglteam dgl-cuda11.3 -y
# transformers-3.0.2-py3-none-any.whl
# RUN /opt/conda/bin/conda install --name aida_tmp transformers==3.0.2


# # aida_tmp
ADD ./event_weaksupervision /event_weaksupervision
RUN /opt/conda/bin/conda create -n aida_tmp python=3.7
RUN /opt/conda/bin/conda install -n aida_tmp pytorch=1.11.0 cudatoolkit=11.3 -c pytorch
# RUN /opt/conda/bin/conda install --name aida_tmp -c huggingface tokenizers=0.10.1 transformers=4.6.1
RUN /opt/conda/bin/conda install --name aida_tmp -c huggingface transformers==4.11.3
RUN /opt/conda/envs/aida_tmp/bin/pip install numpy==1.19.2 tqdm==4.62.2 lxml==4.6.3 flask==2.0.1
# covid entity
ADD ./entity_covid /entity_covid
RUN /opt/conda/envs/aida_tmp/bin/pip install spacy tornado scipy==1.6.2 scikit-learn fairseq 
RUN /opt/conda/envs/aida_tmp/bin/python -m spacy download en_core_web_sm
# detect lang
RUN /opt/conda/envs/aida_tmp/bin/pip install langdetect jieba nltk
RUN /opt/conda/envs/aida_tmp/bin/python -m nltk.downloader popular -d /opt/conda/envs/aida_tmp/share/nltk_data
# # arg amr
# RUN /opt/conda/envs/aida_tmp/bin/pip install fairseq
# RUN /opt/conda/envs/aida_tmp/bin/python -m nltk.downloader averaged_perceptron_tagger universal_tagset -d /opt/conda/envs/aida_tmp/share/nltk_data
# # fine typing
# RUN /opt/conda/envs/aida_tmp/bin/pip install allennlp==0.9.0


# preprocessing using py36
ADD ./postprocessing /postprocessing
RUN cd /postprocessing/AIDA-Interchange-Format-master.m54/python && \
    /opt/conda/envs/genie/bin/python setup.py install

ADD ./preprocessing /preprocessing

ADD ./arg_amr /arg_amr
ADD ./typing /typing
# RUN /opt/conda/bin/conda env create -f /typing/entity_api/aida_entity.yml

# RUN /opt/conda/envs/genie/bin/pip install --upgrade psutil
RUN /opt/conda/bin/conda clean -tipsy

# LABEL maintainer="hengji@illinois.edu"


CMD ["/bin/bash"]

# docker build -t blendernlp/covid-claim-radar:ke .