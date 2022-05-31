from collections import defaultdict
all_data = []
for lan, claim_file in [('en','output_json_en/claim_all_merge_revanth.json'),('es','output_json_es/claim_all_merge_revanth.json'),('ru','output_json_ru/claim_all_merge_revanth.json')]: 
    with open(claim_file,'r') as f:
        import json
        data = json.load(f)

    claimID2data = {v['claim_id']:v for vs in data.values() for v in vs}

    new_data = {'claims':[]}
    for k,vs in data.items():
        for v in vs:
            v['source'] = k
            for e in ['claimer_text','claimer_affiliation','claimer_affiliation_identity_qnode', 'claimer_affiliation_type_qnode','location']:
                if e not in v:
                    v[e] = ''
            v['entity'] = v['claim_semantics'][0][2]
            v['stance'] = v['stance'].capitalize()
            if v['claimer_text']=="<AUTHOR>" and v['news_author']!="":
                v['claimer_text'] = '<AUTHOR>: '+v['news_author']
            
            v['lan'] = lan.upper()
            v['generation'] = 'System'
            if v['topic'] == 'Non-Pharmaceutical Interventions (NPIs): Masks':
                v['topic'] = 'Wearing Masks'

            # Time Attr
            time_attr = {}
            for time_key in ['time_start_earliest','time_start_latest','time_end_earliest','time_end_latest']:
                if time_key in v:
                    if v[time_key]['month'] is not None:
                        month = v[time_key]['month'][-2:]
                    else:
                        month = None
                    
                    if v[time_key]['day'] is not None:
                        day = v[time_key]['day'][-2:]
                    else:
                        day = None
                    if (month is not None) and (day is not None) and (v[time_key]['year'] is not None):
                        time_attr[time_key] = v[time_key]['time_type']['name']+' '+'{}-{}-{}'.format(v[time_key]['year'],month,day)
            v['time_attr'] = '\n'.join([key+': '+val for key, val in time_attr.items()])


            # Sentence LMR
            if v['claim_span_text']!="":
                v['sentence_L'] = v['sentence'][:v['claim_span_start']]
                v['sentence_M'] = v['sentence'][v['claim_span_start']:v['claim_span_end']]
                v['sentence_R'] = v['sentence'][v['claim_span_end']:]
            else:
                v['sentence_L'] = v['sentence']
                v['sentence_M'] = ''
                v['sentence_R'] = ''

            # claim_attr
            for claim_attr in ['equivalent_claims', 'supporting_claims', 'refuting_claims']:
                if claim_attr in v:
                    match_claims = [claimID2data[match_claim_id]['sentence'] for match_claim_id in v[claim_attr] if match_claim_id in claimID2data]
                    v[claim_attr+'_text'] = '\n\n'.join(match_claims)
                else:
                    v[claim_attr+'_text'] = ''

            #claim search key
            if len(v['claimer_ke'])!=0:
                v['claimer_search_key'] = ','.join([e[0] for e in v['claimer_ke']])
                # if v['claimer_text']=="Vincent Racaniello":
                #     print(v['claimer_search_key'])
            else:
                v['claimer_search_key'] = ''

            # v['stance'] = 'assert'
            new_data['claims'].append(v)


    # process inline

    for v in new_data['claims']:
        associated_KEs = v['associated_KEs']

        EntityID2Offset = defaultdict(list)
        for ke in associated_KEs:
            if ke[0].split('_')[1].lower() == 'entity':
                EntityID2Offset[ke[0]].append(ke[3])
        EntityID2Offset = dict(EntityID2Offset)

        new_associated_KEs = []
        with open('rsd_{}/{}.rsd.txt'.format(lan,v['source']),'r') as f:
            rsd_data = f.read()

        relation_kes = {}

        for ke in associated_KEs:
            new_ke = {}
            new_ke['Event'] = ke[0]
            new_ke['Text'] = ke[1]
            new_ke['Relation'] = ke[2]
            new_ke['Offset'] = ke[3]
            new_ke['Url'] = ke[4]
            new_ke['Tooltip'] = True
            class_type = ke[0].split('_')[1].lower()
            assert class_type in ['entity','event','relation']
            new_ke['Class'] = 'class-'+class_type
            new_ke['St'] = int(ke[3].split(':')[1].split('-')[0])
            new_ke['Ed'] = int(ke[3].split(':')[1].split('-')[1])+1
            new_ke['Arg'] = ''
            if ke[5] != '':
                arg = []
                for k1,v1 in ke[5].items():
                    arg_words = []
                    for v1_v in v1.values():
                        pre_arg_words = []
                        for v1_vv in v1_v:
                            arg_word = v1_vv[1]
                            assert arg_word.split(':')[0] == v['source']
                            arg_word = rsd_data[int(arg_word.split(':')[1].split('-')[0]):int(arg_word.split(':')[1].split('-')[1])+1]
                            pre_arg_words.append(arg_word)
                        pre_arg_words = ', '.join(pre_arg_words)
                        arg_words.append(pre_arg_words)

                    to_append = {
                        'Role': k1,
                        'Offset': '^'.join(['^'.join(EntityID2Offset[v_k]) for v_k in v1.keys() if v_k in EntityID2Offset]),
                        'Word': ', '.join(arg_words)
                    }

                    assert type(to_append['Role']) == type("123")
                    assert type(to_append['Offset']) == type("123")
                    if to_append['Offset']!='':
                        # arg.append(to_append)
                        arg.append(to_append['Role']+'@'+to_append['Offset']+'@'+to_append['Word'])
                new_ke['Arg'] = '|'.join(arg)
                assert type(new_ke['Arg']) == type("123")

            if class_type=='relation':
                new_ke['Text'] = rsd_data[new_ke['St']:new_ke['Ed']]
            
                if ke[3] not in relation_kes:
                    relation_kes[ke[3]] = new_ke
                else:
                    relation_kes[ke[3]]['Relation'] = relation_kes[ke[3]]['Relation'] +', ' +new_ke['Relation']
            if class_type!='relation':
                new_associated_KEs.append(new_ke)
        
        new_associated_KEs = new_associated_KEs + list(relation_kes.values())

        # new_associated_KEs.append({
        #     'Event': '',
        #     'Text': v['claimer_text'],
        #     'Relation': '',
        #     'Offset': '',
        #     'Url': '',
        #     'Tooltip': False,
        #     'Class': 'class-claimer',
        #     'St': v['claimer_start'],
        #     'Ed':v['claimer_end']
        # })

        new_associated_KEs = sorted(new_associated_KEs,key=lambda x: x['St'], reverse=False)

        # with open('rsd/{}.rsd.txt'.format(v['source']),'r') as f:
        #     rsd_data = f.read()
        
        black_text = []

        black_text.append({
            'Event': '',
            'Text': rsd_data[max(0,new_associated_KEs[0]['St']-30):new_associated_KEs[0]['St']],
            'Relation': '',
            'Offset': '',
            'Url': '',
            'Tooltip': False,
            'Class': 'class-black',
            'St': max(0,new_associated_KEs[0]['St']-30),
            'Ed': new_associated_KEs[0]['St'],
            'Arg': ''
        })

        if black_text[0]['St']!=0:
            black_text[0]['Text'] = '......' + black_text[0]['Text']
        
        for idx in range(0,len(new_associated_KEs)-1):
            black_text.append({
                'Event': '',
                'Text': rsd_data[new_associated_KEs[idx]['Ed']:new_associated_KEs[idx+1]['St']],
                'Relation': '',
                'Offset': '',
                'Url': '',
                'Tooltip': False,
                'Class': 'class-black',
                'St': new_associated_KEs[idx]['Ed'],
                'Ed': new_associated_KEs[idx+1]['St'],
                'Arg': ''
            })
        

        black_text.append({
            'Event': '',
            'Text': rsd_data[new_associated_KEs[-1]['Ed']:min(len(rsd_data),new_associated_KEs[-1]['Ed']+30)],
            'Relation': '',
            'Offset': '',
            'Url': '',
            'Tooltip': False,
            'Class': 'class-black',
            'St': new_associated_KEs[-1]['Ed'],
            'Ed': min(len(rsd_data),new_associated_KEs[-1]['Ed']+30),
            'Arg': ''
        })

        if black_text[-1]['Ed']!=len(rsd_data):
            black_text[-1]['Text'] = black_text[-1]['Text'] +'......'

        render_text = sorted(new_associated_KEs+black_text, key = lambda x: x['St'], reverse=False)

        v['render_text'] = render_text

        # new_data['claims'][k] = v
    all_data.append(new_data)
all_data = {'claims':all_data[0]['claims']+all_data[1]['claims']+all_data[2]['claims']}

with open('claims.json','w') as f:
    json.dump(all_data,f,indent=4)