import os
import ujson as json
from collections import Counter, defaultdict

def statistics_claim(claim_data_new, entity_data, output_dir):
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

    claim_topic_counter = Counter()
    claim_subtopic_counter = Counter()
    claim_xvariable_counter = Counter()
    # claim_template_counter = Counter()
    claim_claimer_counter = dict() #Counter()
    claim_claimer_affiliation_counter = Counter()
    claim_location_counter = Counter()
    claim_event_counter = Counter()
    claim_entity_counter = Counter()

    for doc_id in claim_data_new:
        for claim in claim_data_new[doc_id]:
            claim_num += 1
            claim_topic_counter[claim['topic']] += 1
            claim_subtopic_counter[claim['sub_topic']] += 1
            claim_xvariable_counter[claim['x_variable']] += 1
            if claim['claimer_start'] != -1:
                if len(claim['claimer_ke']) > 0:
                    claimer_num += 1
                    # claim_claimer_counter[claim['claimer_text']] += 1
                    print(claim['claimer_ke'])
                    for claimer_ke in claim['claimer_ke']:
                        claimer_ke_text, _ = entity_data[claimer_ke[0]]['canonical_mention'][doc_id]
                        # claimer_text = claim['claimer_ke'][0][1]
                        claim_claimer_counter[claimer_ke_text] = claimer_ke[0]
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
                    claim_associatedke_entity += 1
                if 'Event' in ke[0]:
                    claim_associatedke_event += 1
            for ke in claim['claim_semantics']:
                if 'Entity' in ke[0]:
                    claim_semantics_entity += 1
                    claim_entity_counter[ke[2]] += 1
                if 'Event' in ke[0]:
                    claim_semantics_event += 1
                    claim_event_counter[ke[2]] += 1
    print('claim_num', claim_num)
    print('claimer_num', claimer_num, claimer_num / float(claim_num))
    print('claimer_affiliation_num', claimer_affiliation_num, claimer_affiliation_num / float(claim_num))
    print('claimloc_num', claimloc_num, claimloc_num / float(claim_num))
    print('claimtime_start_earliest_num', claimtime_start_earliest_num, claimtime_start_earliest_num / float(claim_num))
    print('claimtime_start_latest_num', claimtime_start_latest_num, claimtime_start_latest_num / float(claim_num))
    print('claimtime_end_earliest_num', claimtime_end_earliest_num, claimtime_end_earliest_num / float(claim_num))
    print('claimtime_end_latest_num', claimtime_end_latest_num, claimtime_end_latest_num / float(claim_num))
    print('claim_associatedke_entity', claim_associatedke_entity, claim_associatedke_entity / float(claim_num))
    print('claim_associatedke_event', claim_associatedke_event, claim_associatedke_event / float(claim_num))
    print('claim_semantics_entity', claim_semantics_entity, claim_semantics_entity / float(claim_num))
    print('claim_semantics_event', claim_semantics_event, claim_semantics_event / float(claim_num))

    json.dump(claim_topic_counter, open(os.path.join(output_dir, 'claim_topic_counter.json'), 'w'), indent=4)
    json.dump(claim_subtopic_counter, open(os.path.join(output_dir, 'claim_subtopic_counter.json'), 'w'), indent=4)
    json.dump({key:value for key,value in claim_xvariable_counter.most_common()}, open(os.path.join(output_dir, 'claim_xvariable_counter.json'), 'w'), indent=4)
    # json.dump({key:value for key,value in claim_claimer_counter.most_common()}, open(os.path.join(output_dir, 'claim_claimer_counter.json'), 'w'), indent=4)
    json.dump(claim_claimer_counter, open(os.path.join(output_dir, 'claim_claimer_counter.json'), 'w'), indent=4)
    json.dump({key:value for key,value in claim_claimer_affiliation_counter.most_common()}, open(os.path.join(output_dir, 'claim_claimer_affiliation_counter.json'), 'w'), indent=4)
    json.dump({key:value for key,value in claim_location_counter.most_common()}, open(os.path.join(output_dir, 'claim_location_counter.json'), 'w'), indent=4)
    json.dump({key:value for key,value in claim_event_counter.most_common()}, open(os.path.join(output_dir, 'claim_event_counter.json'), 'w'), indent=4)
    json.dump({key:value for key,value in claim_entity_counter.most_common()}, open(os.path.join(output_dir, 'claim_entity_counter.json'), 'w'), indent=4)


if __name__=='__main__':
    # claim_json = '/shared/nas/data/m1/revanth3/exp/claims/exp/acl_demo/claim_all_stance_authinfo_eqcl_sup_ref.json'
    claim_json = '/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/ru/output_ttl/claim_all_merge_revanth.json'
    entity_json = '/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/ru/final/entity_info.json'
    output_dir = '/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/ru/output_json'
    os.makedirs(output_dir, exist_ok=True)
    claim_data_new = json.load(open(claim_json))
    entity_data = json.load(open(entity_json))
    statistics_claim(claim_data_new, entity_data, output_dir)