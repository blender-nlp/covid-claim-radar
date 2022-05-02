#!/usr/bin/env bash -e

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 data_root query_root parent_child_tab_path gpu_device"
    exit 1
fi

lang=en
data_root=$1  # the directory contains ltf and rsd subdirectories
query_root=$2 # Condition 5 query directory
parent_child_tab_path=$3 # /shared/nas/data/m1/AIDA_Data/LDC_raw_data/LDC2021E11_AIDA_Phase_3_Practice_Topic_Source_Data_V2.0/docs/parent_children.tab
gpu_device=$4

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
dir_count=$(ls ${data_root} | wc -l)
if [ "$dir_count" -ne "2" ]; then
    echo "unexpected dirs under ${data_root}; only ltf nd rsd allowed"
    exit 1
fi

# ltf source folder path
ltf_source=${data_root}/ltf

# oneie
ie_dir=${data_root}/merge
ie_event_cs=${ie_dir}/cs/event.cs
ie_entity_cs=${ie_dir}/cs/entity.cs
ie_relation_cs=${ie_dir}/cs/relation.cs
# qnode linking
qnode_dir=${data_root}/qnode
mkdir -p ${qnode_dir}
el_results_cs=${qnode_dir}/el_entity.cs
el_results_tab=${qnode_dir}/el_entity.tab
entity_coref_results_cs=${qnode_dir}/coref_entity.cs
entity_coref_results_tab=${qnode_dir}/coref_entity.tab
event_coref_results_cs=${qnode_dir}/coref_event.cs
event_coref_results_tab=${qnode_dir}/coref_event.tab
final_entity_cs=${qnode_dir}/final_entity.cs
final_relation_cs=${qnode_dir}/final_relation.cs
near_final_event_cs=${qnode_dir}/near_final_event.cs
final_event_cs=${qnode_dir}/final_event.cs
final_cs=${qnode_dir}/final_merged.cs
ttl_output=${data_root}/ttl_output
# claim output
claim_dir=${data_root}/claim
claim_json=${claim_dir}/claim_output.json
claim_qnode_json=${claim_dir}/claims_qnode.json


######################################################
# Set up
######################################################
docker run -d --net=host -e "discovery.type=single-node" laituan245/wikidata-es

######################################################
# Information Extraction
######################################################
# Information Extraction for entities, relations and events
docker run --rm -i -v ${data_root}:${data_root} -w /oneie --gpus device=${gpu_device} limteng/oneie_aida_m36 \
    /opt/conda/bin/python \
    /oneie/predict.py -i ${ltf_source} -o ${data_root} -l ${lang}

######################################################
# Claim Extraction
######################################################
docker run  --rm --gpus 1 -v ${data_root}:/var/spool/input/ -v ${query_root}:/var/spool/topics/ -v ${claim_dir}:/var/spool/output/ -t blendernlp/covid-claim-radar:revanth3_aida_claim_v2

######################################################
# Qnode linking
######################################################
# Entity Linking
docker run --net=host --gpus device=${gpu_device} --rm -v ${data_root}:${data_root} laituan245/wikidata_el:aida2022 \
           --input_cs=${ie_entity_cs}                   \
           --ltf_dir=${ltf_source}                         \
	   --output_cs=${el_results_cs}                 \
	   --output_tab=${el_results_tab}


# Entity Coreference
docker run --gpus device=${gpu_device} --rm -v ${data_root}:${data_root} laituan245/spanbert_entity_coref:aida2022 \
                               --edl_official=${el_results_tab}   \
                               --edl_freebase=${el_results_tab}   \
			       --ltf_dir=${ltf_source}               \
                               --output_tab=${entity_coref_results_tab} \
			       --output_cs=${entity_coref_results_cs}

# Event Coreference
docker run --gpus device=${gpu_device} --rm -v ${data_root}:${data_root} laituan245/spanbert_coref \
	                       --input=${ie_event_cs} \
			       --cs_file=${event_coref_results_cs} \
			       --tab_file=${event_coref_results_tab} \
			       --ltf_dir=${ltf_source}


# Add type qnode
docker run --net=host --rm -v ${data_root}:${data_root} laituan245/add_types_qnode \
           --cs_fp=${entity_coref_results_cs} \
           --output_fp=${final_entity_cs}

# Rewrite ids of entities in relation.cs
docker run --rm -v ${data_root}:${data_root} laituan245/aida_postprocess \
	   /opt/conda/envs/aida_coreference/bin/python3.6 rewrite_relation.py \
	  --old_relation_cs=${ie_relation_cs} \
	  --old_entity_cs=${ie_entity_cs}     \
	  --new_entity_cs=${entity_coref_results_cs} \
	  --new_relation_cs=${final_relation_cs}

# Write ids of entities in entity.cs
docker run --rm -v ${data_root}:${data_root} laituan245/aida_postprocess \
	    /opt/conda/envs/aida_coreference/bin/python3.6 rewrite_event.py \
	    --event_cs=${event_coref_results_cs}  \
	    --final_entity_cs=${final_entity_cs}   \
            --final_event_cs=${near_final_event_cs}

# Event attributes classifier
docker run --rm -v ${data_root}:${data_root} laituan245/aida_attrs_classify \
	   --input=${near_final_event_cs} \
	   --output=${final_event_cs} \
	   --ltf_dir=${ltf_source}

# claimer Qnode linking
docker run --net=host --gpus ${gpu_device} --rm -v ${data_root}:${data_root} laituan245/wikidata_el_demo:covid-claim-radar --input_fp ${claim_json} --output_fp ${claim_qnode_json}

# TODO: this needs to be inside a container
# AIF converter
cat ${final_entity_cs} ${final_relation_cs} ${final_event_cs} > ${final_cs}
docker run --rm -v ${final_cs}:${final_cs} -v ${ltf_source}:${ltf_source} -v ${ttl_output}:${ttl_output} -v ${parent_child_tab_path}:${parent_child_tab_path} -v ${claim_qnode_json}:${claim_qnode_json} blendernlp/covid-claim-radar:ke \
	/opt/conda/envs/genie/bin/python /postprocessing/aif_claim.py --input_cs ${final_cs} --ltf_dir ${ltf_source} \
    --output_ttl_dir ${ttl_output} --lang ${lang} --eval m36 \
    --parent_child_tab_path ${parent_child_tab_path} \
    --claim_json ${claim_qnode_json} \
    --overlay /postprocessing/params/xpo_v4.1_draft.json
    # --trans_json ${trans_json} 
    # --str_mapping_file ${str_mapping_file}

chmod -R 777 ${ttl_output}
echo ${ttl_output}

