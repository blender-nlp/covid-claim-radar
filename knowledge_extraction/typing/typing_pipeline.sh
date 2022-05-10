lang=$1
ltf_source=$2
rsd_source=$3
core_nlp_output_path=$4
input_entity=$5
input_relation=$6
input_event=$7
filler_coarse=$8
output_entity=$9
output_relation=${10}
output_event=${11}


new_relation_coarse=${input_relation}_filler.cs
/opt/conda/envs/genie/bin/python /typing/aida_filler/extract_filler_relation.py \
    --corenlp_dir ${core_nlp_output_path} \
    --ltf_dir ${ltf_source} \
    --edl_path ${input_entity} \
    --text_dir ${rsd_source} \
    --path_relation ${new_relation_coarse} \
    --path_filler ${filler_coarse} \
    --lang ${lang}

cat ${input_entity} ${filler_coarse} > ${output_entity}_tmp
/opt/conda/envs/genie/bin/python /typing/match_ltf.py \
    --ltf_dir ${ltf_source} \
    --rsd_dir ${rsd_source} \
    --input_cs ${output_entity}_tmp \
    --output_cs ${output_entity}

cat ${input_relation} ${new_relation_coarse} > ${output_relation}

cat ${input_event} > ${output_event}