import os
import ujson as json
from collections import Counter, defaultdict

def statistics_claim(claim_data_new, entity_data, output_dir=None, rsd_dir=None):
    claim_num = 0
    claimer_num = 0
    claimer_affiliation_num = 0
    claimloc_num = 0
    claimtime_start_earliest_num = 0
    claimtime_start_latest_num = 0
    claimtime_end_earliest_num = 0
    claimtime_end_latest_num = 0
    claim_associatedke_entity = 0
    claim_associatedke_event = 0
    claim_semantics_entity = 0
    claim_semantics_event = 0
    claim_associatedke_noevent = 0
    claim_semantics_noevent = 0

    claim_topic_counter = Counter()
    claim_subtopic_counter = Counter()
    claim_xvariable_counter = Counter()
    # claim_template_counter = Counter()
    claim_claimer_counter = Counter()#dict() #
    claim_claimer_affiliation_counter = Counter()
    claim_location_counter = Counter()
    claim_event_counter = Counter()
    claim_entity_counter = Counter()

    for doc_id in claim_data_new:
        for claim in claim_data_new[doc_id]:
            singleclaim_associatedke_entity = 0
            singleclaim_associatedke_event = 0
            singleclaim_semantics_entity = 0
            singleclaim_semantics_event = 0
            claim_num += 1
            claim_topic_counter[claim['topic']] += 1
            claim_subtopic_counter[claim['sub_topic']] += 1
            claim_xvariable_counter[claim['x_variable']] += 1
            if claim['claimer_start'] != -1:
                if len(claim['claimer_ke']) > 0:
                    claimer_num += 1
                    claim_claimer_counter[claim['claimer_text']] += 1
                    # print(claim['claimer_ke'])
                    # for claimer_ke in claim['claimer_ke']:
                    #     claimer_ke_text, _ = entity_data[claimer_ke[0]]['canonical_mention'][doc_id]
                    #     # claimer_text = claim['claimer_ke'][0][1]
                    #     claim_claimer_counter[claimer_ke_text] = claimer_ke[0]
            if 'claimer_affiliation' in claim:
                claimer_affiliation_num += 1
                claim_claimer_affiliation_counter[claim['claimer_affiliation']] += 1
            if 'location' in claim:
                claimloc_num += 1
                claim_location_counter[claim['location']] += 1
            if 'time_start_earliest' in claim:
                claimtime_start_earliest_num += 1
            if 'time_start_latest' in claim:
                claimtime_start_latest_num += 1
            if 'time_end_earliest' in claim:
                claimtime_end_earliest_num += 1
            if 'time_end_latest' in claim:
                claimtime_end_latest_num += 1
            for ke in claim['associated_KEs']:
                if 'Entity' in ke[0]:
                    singleclaim_associatedke_entity += 1
                if 'Event' in ke[0] or 'Relation' in ke[0]:
                    singleclaim_associatedke_event += 1
            claim_associatedke_entity += singleclaim_associatedke_entity
            claim_associatedke_event += singleclaim_associatedke_event
            if singleclaim_associatedke_event == 0:
                claim_associatedke_noevent += 1
                # print(claim['claim_id'])
                if output_dir is not None:
                    output_file = os.path.join(output_dir, 'no_associatedKE_%s.json' % claim['claim_id'])
                    if rsd_dir is not None:
                        claim['rsd'] = open(os.path.join(rsd_dir, doc_id+'.rsd.txt')).read()
                    json.dump(claim, open(output_file, 'w'), indent=4)
            for ke in claim['claim_semantics']:
                if 'Entity' in ke[0]:
                    singleclaim_semantics_entity += 1
                    claim_entity_counter[ke[2]] += 1
                if 'Event' in ke[0] or 'Relation' in ke[0]:
                    singleclaim_semantics_event += 1
                    claim_event_counter[ke[2]] += 1
            claim_semantics_entity += singleclaim_semantics_entity
            claim_semantics_event += singleclaim_semantics_event
            if singleclaim_semantics_event == 0:
                claim_semantics_noevent += 1
                if output_dir is not None:
                    output_file = os.path.join(output_dir, 'no_claimsemantics_%s.json' % claim['claim_id'])
                    if rsd_dir is not None:
                        claim['rsd'] = open(os.path.join(rsd_dir, doc_id+'.rsd.txt')).read()
                    json.dump(claim, open(output_file, 'w'), indent=4)
                
            
    print('doc_num', len(claim_data_new))
    print('claim_num', claim_num)
    print('claimer_num', claimer_num, '%.2f' % (claimer_num / float(claim_num)))
    print('claimer_affiliation_num', claimer_affiliation_num, '%.2f' % (claimer_affiliation_num / float(claim_num)))
    print('claimloc_num', claimloc_num, '%.2f' % (claimloc_num / float(claim_num)))
    print('claimtime_start_earliest_num', claimtime_start_earliest_num, '%.2f' % (claimtime_start_earliest_num / float(claim_num)))
    print('claimtime_start_latest_num', claimtime_start_latest_num, '%.2f' % (claimtime_start_latest_num / float(claim_num)))
    print('claimtime_end_earliest_num', claimtime_end_earliest_num, '%.2f' % (claimtime_end_earliest_num / float(claim_num)))
    print('claimtime_end_latest_num', claimtime_end_latest_num, '%.2f' % (claimtime_end_latest_num / float(claim_num)))
    print('claim_associatedke_entity', claim_associatedke_entity, '%.2f' % (claim_associatedke_entity / float(claim_num)))
    print('claim_associatedke_event', claim_associatedke_event, '%.2f' % (claim_associatedke_event / float(claim_num)))
    print('claim_semantics_entity', claim_semantics_entity, '%.2f' % (claim_semantics_entity / float(claim_num)))
    print('claim_semantics_event', claim_semantics_event, '%.2f' % (claim_semantics_event / float(claim_num)))
    print('claim_associatedke_noevent', claim_associatedke_noevent)
    print('claim_semantics_noevent', claim_semantics_noevent)
    # json.dump(claim_topic_counter, open(os.path.join(output_dir, 'claim_topic_counter.json'), 'w'), indent=4)
    # json.dump(claim_subtopic_counter, open(os.path.join(output_dir, 'claim_subtopic_counter.json'), 'w'), indent=4)
    # json.dump({key:value for key,value in claim_xvariable_counter.most_common()}, open(os.path.join(output_dir, 'claim_xvariable_counter.json'), 'w'), indent=4)
    # # json.dump({key:value for key,value in claim_claimer_counter.most_common()}, open(os.path.join(output_dir, 'claim_claimer_counter.json'), 'w'), indent=4)
    # json.dump(claim_claimer_counter, open(os.path.join(output_dir, 'claim_claimer_counter.json'), 'w'), indent=4)
    # json.dump({key:value for key,value in claim_claimer_affiliation_counter.most_common()}, open(os.path.join(output_dir, 'claim_claimer_affiliation_counter.json'), 'w'), indent=4)
    # json.dump({key:value for key,value in claim_location_counter.most_common()}, open(os.path.join(output_dir, 'claim_location_counter.json'), 'w'), indent=4)
    # json.dump({key:value for key,value in claim_event_counter.most_common()}, open(os.path.join(output_dir, 'claim_event_counter.json'), 'w'), indent=4)
    # json.dump({key:value for key,value in claim_entity_counter.most_common()}, open(os.path.join(output_dir, 'claim_entity_counter.json'), 'w'), indent=4)


if __name__=='__main__':
    # claim_json = '/shared/nas/data/m1/revanth3/exp/claims/exp/acl_demo/claim_all_stance_authinfo_eqcl_sup_ref.json'
    
    # claim_json = '/shared/nas/data/m1/revanth3/exp/claims/exp/docker/eval_es_output/condition_5/claim_output_v2.json'
    # claim_json = '/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/LDC2022R02/en/output_ttl_condition_5/claim_all.json'
    claim_json = '/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/LDC2022R02/en/eval_en_condition_5_highrecall_moreedge_v7/claim_all.json'
    output_dir = claim_json.replace('/claim_all.json', '_claim_vis')
    # entity_json = '/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/ru/final/entity_info.json'
    rsd_dir = None #'/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/LDC2022R02/en/rsd'
    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
    claim_data_new = json.load(open(claim_json))
    entity_data = None #json.load(open(entity_json))

    print(claim_json)
    statistics_claim(claim_data_new, entity_data, output_dir,rsd_dir)