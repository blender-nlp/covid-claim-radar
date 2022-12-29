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

# # fine-grained entity
# /opt/conda/envs/aida_entity/bin/python /typing/entity_api/typing_m36.py \
#     --ltf_input ${ltf_source} --output ${input_entity}.tsv

# COVID entity detection
input_entity_covid=${input_entity}_covid
/opt/conda/envs/aida_tmp/bin/python /entity_covid/process.py \
    --ltf ${ltf_source} --entity ${input_entity} --out ${input_entity_covid}

oneie_input=${input_entity//"cs/entity.cs"/"json"}
intermediate_dir=${core_nlp_output_path//corenlp/weakevent}
# extract more triggers
/opt/conda/envs/aida_tmp/bin/python /event_weaksupervision/run_event_detection.py \
    --input_dir ${oneie_input} \
    --output_dir ${intermediate_dir} \
    --input_type doc \
    --resource_dir /event_weaksupervision/resources/models/covid

# extract args using AMR
/opt/conda/envs/aida_tmp/bin/python /arg_amr/extract.py \
      --data_file ${intermediate_dir}/docs.ann.jsonl \
      --json_output ${intermediate_dir}/docs.args.jsonl \
      --visual_output ${intermediate_dir}/visualization.jsonl
# merge results
/opt/conda/envs/aida_tmp/bin/python /event_weaksupervision/convert_outputs.py \
    --input_dir ${oneie_input} \
    --output_dir ${intermediate_dir} \
    --input_type doc \
    --resource_dir /event_weaksupervision/resources/models/covid \
    --merged_ent_cs ${input_entity_covid}/entity.cs
/opt/conda/envs/aida_tmp/bin/python /event_weaksupervision/run_conversion.py \
    --output_dir ${intermediate_dir}

# extract fillers
new_relation_coarse=${input_relation}_filler.cs
/opt/conda/envs/genie/bin/python /typing/aida_filler/extract_filler_relation.py \
    --corenlp_dir ${core_nlp_output_path} \
    --ltf_dir ${ltf_source} \
    --edl_path ${input_entity} \
    --text_dir ${rsd_source} \
    --path_relation ${new_relation_coarse} \
    --path_filler ${filler_coarse} \
    --lang en

# extract generation-based args
genie_dir=${core_nlp_output_path//corenlp/gen_arg}
/opt/conda/envs/genie/bin/python /arg_genie/test_cs.py --model=pointer \
    --ckpt_name=${genie_dir}/ckpt \
    --tmp_dir=${genie_dir}/tmp \
    --input_dir=${intermediate_dir} \
    --dataset=combined \
    --ontology_file=/arg_genie/event_role_AIDA_P2.json \
    --load_ckpt=/arg_genie/models/gen-combined.ckpt \
    --eval_batch_size=4 \
    --mark_trigger \
    --eval_only \
    --gpus=0
/opt/conda/envs/genie/bin/python /arg_genie/genie/convert_gen_to_cs.py \
    --ontology_file=/arg_genie/event_role_AIDA_P2.json \
    --gen_file=${genie_dir}/ckpt/predictions.jsonl \
    --input_dir=${intermediate_dir} \
    --merged_file=${genie_dir}/ckpt/merged.jsonl \
    --diff_file=${genie_dir}/ckpt/diff.json


cat ${intermediate_dir}/cs/entity.cs ${intermediate_dir}/entity.aug.cs ${filler_coarse} > ${output_entity}_tmp
/opt/conda/envs/genie/bin/python /typing/match_ltf.py \
    --ltf_dir ${ltf_source} \
    --rsd_dir ${rsd_source} \
    --input_cs ${output_entity}_tmp \
    --output_cs ${output_entity}

cat ${intermediate_dir}/cs/relation.cs ${new_relation_coarse} > ${output_relation}

cat ${intermediate_dir}/event.aug.cs > ${output_event}

mkdir -p ${core_nlp_output_path//corenlp/claim}