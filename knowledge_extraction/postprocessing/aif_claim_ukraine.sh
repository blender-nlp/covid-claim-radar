# /opt/conda/envs/genie/bin/python /EventTimeArg/aida_event_time_pipeline.py \
#     --time_cold_start_filename ${input_filler} \
#     --event_cold_start_filename ${input_event} \
#     --read_cs_event \
#     --parent_children_filename ${parent_child_tab} \
#     --ltf_path ${data_root}/ltf \
#     --output_filename ${final_event_cs} \
#     --use_dct_as_default \
#     --lang en

# docker run --gpus device=0 --rm -v /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar:/shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar blendernlp/covid-claim-radar:ke \
# /opt/conda/envs/genie/bin/python /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/knowledge_extraction/postprocessing/aif_claim_ukraine.py \
#     --input_cs /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine/en/qnode/final_all.cs \
#     --ltf_dir /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine/en/ltf \
#     --output_ttl_dir /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine/en/ttl \
#     --lang en \
#     --eval m36 \
#     --parent_child_tab_path /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine/en/parent_children.tab \
#     --claim_json /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine/en/claim/claim_with_claimer_v2.json \
#     --overlay /postprocessing/params/xpo_v4.1_draft.json 


docker run --gpus device=0 --rm -v /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar:/shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar blendernlp/covid-claim-radar:ke \
/opt/conda/envs/genie/bin/python /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/knowledge_extraction/postprocessing/aif_claim_ukraine.py \
    --input_cs /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/en/weakevent/all.cs \
    --ltf_dir /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/en/ltf \
    --output_ttl_dir /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/en/ttl \
    --lang en \
    --eval m36 \
    --parent_child_tab_path /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/en/parent_children.tab \
    --claim_json /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/en/claim/output_rerank.json \
    --overlay /postprocessing/params/xpo_v4.1_draft.json 