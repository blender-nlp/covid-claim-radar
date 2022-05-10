rsd_source=$1
ltf_source=$2
rsd_file_list=$3
core_nlp_output_path=$4

# echo ${core_nlp_output_path}
/opt/conda/envs/genie/bin/python /preprocessing/dir_readlink.py ${rsd_source} ${rsd_file_list} --stanford_corenlp ${core_nlp_output_path}

