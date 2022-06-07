#!/usr/bin/env bash -e

if [ "$#" -ne 5 ]; then
    echo "Usage: $0 lang data_root query_root parent_child_tab_path gpu_device"
    exit 1
fi

lang=$1
data_root=$2  # the directory contains ltf and rsd subdirectories
query_root=$3 # Condition 5 query directory
parent_child_tab_path=$4 # LDC2021E11_AIDA_Phase_3_Practice_Topic_Source_Data_V2.0/docs/parent_children.tab
gpu_device=$5

######################################################
# Arguments
######################################################

if [ ! -e ${data_root}/ltf ]; then
    echo "missing ${data_root}/ltf"
    exit 1
fi
if [ ! -e ${data_root}/rsd ]; then
    echo "missing ${data_root}/rsd"
    exit 1
fi

# ltf source folder path
ltf_source=${data_root}/ltf
rsd_source=${data_root}/rsd
rsd_file_list=${data_root}/rsd_lst

# oneie
ie_dir=${data_root}/merge
oneie_event_cs=${ie_dir}/cs/event.cs
oneie_entity_cs=${ie_dir}/cs/entity.cs
oneie_relation_cs=${ie_dir}/cs/relation.cs
ie_event_cs=${ie_dir}/cs/event_nocoref_final.cs
ie_entity_cs=${ie_dir}/cs/entity_nocoref_final.cs
ie_relation_cs=${ie_dir}/cs/relation_nocoref_final.cs
filler_coarse=${ie_dir}/cs/filler.cs
core_nlp_output_path=${data_root}/corenlp
genie_dir=${data_root}/genie
# qnode linking
qnode_dir=${data_root}/qnode
docker run --rm -v ${data_root}:${data_root} blendernlp/covid-claim-radar:ke mkdir -p ${qnode_dir}
el_results_cs=${qnode_dir}/el_entity.cs
el_results_tab=${qnode_dir}/el_entity.tab
entity_coref_results_cs=${qnode_dir}/coref_entity.cs
entity_coref_results_tab=${qnode_dir}/coref_entity.tab
event_coref_results_cs=${qnode_dir}/coref_event.cs
event_coref_results_tab=${qnode_dir}/coref_event.tab
final_entity_cs=${qnode_dir}/final_entity.cs
final_relation_cs=${qnode_dir}/final_relation.cs
final_event_cs=${qnode_dir}/final_event.cs
final_cs=${qnode_dir}/final_all.cs
ttl_output=${data_root}/ttl_output
# claim output
claim_dir=${data_root}/claim
claim_json=${claim_dir}/claim_output.json
claim_qnode_json=${claim_dir}/claims_qnode.json


# #####################################################
# # pulling dockers
# #####################################################
# docker pull limteng/oneie_aida_m36
# docker pull blendernlp/covid-claim-radar:ke
# docker pull limanling/aida-tools
# docker pull blendernlp/covid-claim-radar:revanth3_aida_claim_v2
# docker pull laituan245/wikidata_el_demo_with_es:covid-claim-radar
# docker pull laituan245/wikidata_el_with_es:aida2022
# docker pull laituan245/spanbert_entity_coref:aida2022
# docker pull laituan245/spanbert_coref
# docker pull laituan245/add_types_qnode_with_es
# docker pull laituan245/aida_postprocess
# echo $(date)


######################################################
# Information Extraction
######################################################
# Information Extraction for entities, relations and events
docker run --rm -i -v ${data_root}:${data_root} -w /oneie --gpus device=${gpu_device} limteng/oneie_aida_m36 \
    /opt/conda/bin/python \
    /oneie/predict.py -i ${ltf_source} -o ${data_root} -l en
echo "oneie timecount"
echo $(date)
# Time augmentation
docker run --gpus device=${gpu_device} --rm -v ${data_root}:${data_root} -i blendernlp/covid-claim-radar:ke \
    /bin/bash /preprocessing/preprocess.sh ${rsd_source} ${ltf_source} ${rsd_file_list} ${core_nlp_output_path}
docker run --rm -v ${data_root}:${data_root} -w /stanford-corenlp-aida_0 -i limanling/aida-tools \
    java -mx50g -cp '/stanford-corenlp-aida_0/*' edu.stanford.nlp.pipeline.StanfordCoreNLP \
    $* -annotators 'tokenize,ssplit,pos,lemma,ner' \
    -outputFormat json \
    -filelist ${rsd_file_list} \
    -properties StanfordCoreNLP_en.properties \
    -outputDirectory ${core_nlp_output_path}
echo "stanford timecount"
echo $(date)
docker run --gpus device=${gpu_device} --rm -v ${data_root}:${data_root} -i blendernlp/covid-claim-radar:ke \
    /bin/bash /typing/typing_pipeline.sh \
    en ${ltf_source} ${rsd_source} ${core_nlp_output_path} ${oneie_entity_cs} ${oneie_relation_cs} ${oneie_event_cs} ${filler_coarse} ${ie_entity_cs} ${ie_relation_cs} ${ie_event_cs}
echo "typing timecount"
echo $(date)

######################################################
# Claim Extraction
######################################################
docker run --rm --gpus device=${gpu_device} -v ${data_root}:/var/spool/input/ -v ${query_root}:/var/spool/topics/ -v ${claim_dir}:/var/spool/output/ -t blendernlp/covid-claim-radar:revanth3_aida_claim_v2
echo "claim timecount"
echo $(date)

######################################################
# Qnode linking
######################################################
# claimer Qnode linking
docker run --gpus ${gpu_device} --rm -v ${data_root}:${data_root} \
           --entrypoint /bin/bash laituan245/wikidata_el_demo_with_es:covid-claim-radar \
           process_claims.sh ${claim_json} ${claim_qnode_json}
echo "claimer timecount"
echo $(date)

# Entity Linking
docker run --gpus device=${gpu_device} --rm -v ${data_root}:${data_root} \
           --entrypoint /bin/bash laituan245/wikidata_el_with_es:aida2022 \
           aida_inference.sh ${ie_entity_cs} ${ltf_source} \
           ${el_results_cs} ${el_results_tab}
echo "linking timecount"
echo $(date)

# Entity Coreference
docker run --gpus device=${gpu_device} --rm -v ${data_root}:${data_root} laituan245/spanbert_entity_coref:aida2022 \
                               --edl_official=${el_results_tab}   \
                               --edl_freebase=${el_results_tab}   \
                   --ltf_dir=${ltf_source}               \
                               --output_tab=${entity_coref_results_tab} \
                   --output_cs=${entity_coref_results_cs}
echo "entity coreference timecount"
echo $(date)

# Event Coreference
docker run --gpus device=${gpu_device} --rm -v ${data_root}:${data_root} laituan245/spanbert_coref \
                           --input=${ie_event_cs} \
                   --cs_file=${event_coref_results_cs} \
                   --tab_file=${event_coref_results_tab} \
                   --ltf_dir=${ltf_source}
echo "event coreference timecount"
echo $(date)

# Add type qnode
docker run --rm -v ${data_root}:${data_root} --entrypoint /bin/bash \
           laituan245/add_types_qnode_with_es \
           add_type_qnodes.sh ${entity_coref_results_cs} ${final_entity_cs}
echo "qnode timecount"
echo $(date)

# Rewrite ids of entities in relation.cs
docker run --rm -v ${data_root}:${data_root} laituan245/aida_postprocess \
       /opt/conda/envs/aida_coreference/bin/python3.6 rewrite_relation.py \
      --old_relation_cs=${ie_relation_cs} \
      --old_entity_cs=${ie_entity_cs}     \
      --new_entity_cs=${entity_coref_results_cs} \
      --new_relation_cs=${final_relation_cs}
echo "rewrite timecount"
echo $(date)

# Write ids of entities in entity.cs
docker run --rm -v ${data_root}:${data_root} laituan245/aida_postprocess \
        /opt/conda/envs/aida_coreference/bin/python3.6 rewrite_event.py \
        --event_cs=${event_coref_results_cs}  \
        --final_entity_cs=${final_entity_cs}   \
        --final_event_cs=${final_event_cs}
echo "rewrite timecount"
echo $(date)

# AIF converter
docker run --gpus device=${gpu_device} --rm -v ${data_root}:${data_root} -v ${parent_child_tab_path}:${parent_child_tab_path} blendernlp/covid-claim-radar:ke \
    /bin/bash /postprocessing/postprocessing.sh \
    ${lang} ${data_root} ${parent_child_tab_path} ${claim_qnode_json} ${final_entity_cs} ${final_relation_cs} ${final_event_cs} ${filler_coarse} ${final_cs} ${ttl_output}

echo "aif timecount"
echo $(date)