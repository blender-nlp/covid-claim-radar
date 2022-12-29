# Claim Extraction

### Installation

You can setup the conda environment using the following command:

```
conda env create -f environment.yml
```

### Running instructions

You need to first get a key to the claimbuster system [here](https://idir.uta.edu/claimbuster/api/request/key/).

A sample topics file is provided in `sample_topics.tsv`

The command to run the code is 
```
python run.py --topics_file <path to file contains topics> \
    --input_dir ${INPUT_DIR} --topic_model_path <path to qa model for topic filtering> \
    --attribute_model_path <path to qa model for extracting background attributes> --output_dir ${OUTPUT_DIR} --claimbuster_key <claimbuster_api_key> \
    --use_gpu
```

`INPUT_DIR` should be path to a folder that contains folders named `rsd` and `ltf`.

The `rsd` folder contains a list of news articles named in the format `<doc_id>.rsd.txt`

To create the `ltf` folder from the `rsd` folder, you can run the first command from [here](https://github.com/limanling/uiuc_ie_pipeline_fine_grained#running-on-raw-text-data).