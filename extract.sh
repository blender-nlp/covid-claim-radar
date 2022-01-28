lang=es
edl_cs=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/${lang}/final/final_entity.cs
rel_cs=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/${lang}/final/final_relation.cs
evt_cs=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/${lang}/event/events_4tuple.cs #final/final_event.cs
merged_cs_link=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/${lang}/final/all.cs
cat ${edl_cs} ${rel_cs} ${evt_cs} > ${merged_cs_link}
ltf_source=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/${lang}/ltf
ttl_initial=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/${lang}/output_ttl
claim_json=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/${lang}/final/claim_with_claimer_and_qnodes.json
trans_json=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/${lang}/sentchar_trans2raw_${lang}.json

xpo_json=/shared/nas/data/m1/manling2/aida_docker/docker_m18/postprocessing/params/xpo_v4_to_be_checked4.json

parent_child_tab_path="/shared/nas/data/m1/AIDA_Data/LDC_raw_data/LDC2021E11_AIDA_Phase_3_Practice_Topic_Source_Data_V2.0/docs/parent_children.tab"

python aif_claim.py --input_cs ${merged_cs_link} --ltf_dir ${ltf_source} \
    --output_ttl_dir ${ttl_initial} --lang ${lang} --eval m36 \
    --parent_child_tab_path ${parent_child_tab_path} \
    --claim_json ${claim_json} \
    --overlay ${xpo_json} --trans_json ${trans_json}

chmod -R 777 ${ttl_initial}
echo ${ttl_initial}