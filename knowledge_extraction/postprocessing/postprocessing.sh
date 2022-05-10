lang=$1
data_root=$2
parent_child_tab=$3
claim_qnode_json=$4
input_entity=$5
input_relation=$6
input_event=$7
input_filler=$8
output_final_cs=$9
output_ttl=${10}

final_event_cs=${data_root}/qnode/final_event_4tuple.cs


echo "event 4 tuple"
/opt/conda/envs/aida_tmp/bin/python /EventTimeArg/aida_event_time_pipeline.py \
    --time_cold_start_filename ${input_filler} \
    --event_cold_start_filename ${input_event} \
    --read_cs_event \
    --parent_children_filename ${parent_child_tab} \
    --ltf_path ${data_root}/ltf \
    --output_filename ${final_event_cs} \
    --use_dct_as_default \
    --lang ${lang}

# merge results
cat ${input_entity} ${input_relation} ${final_event_cs} > ${output_final_cs}

# AIF converter
/opt/conda/envs/genie/bin/python /postprocessing/aif_claim.py \
    --input_cs ${output_final_cs} --ltf_dir ${data_root}/ltf \
    --output_ttl_dir ${output_ttl} --lang ${lang} --eval m36 \
    --parent_child_tab_path ${parent_child_tab} \
    --claim_json ${claim_qnode_json} \
    --overlay /postprocessing/params/xpo_v4.1_draft.json \
    --trans_json ${data_root}/sentchar_trans2raw_${lang}.json \
    --str_mapping_file ${data_root}/name_translate_${lang}.txt

chmod -R 777 ${output_ttl}
echo ${output_ttl}