import json
from collections import defaultdict

claimers = defaultdict(list)

for lan in ['en','es','ru']:
    dir_ = 'output_json_'+lan+'/' 
    with open(dir_+'claim_claimer_counter.json','r') as f:
        lan_claimers = json.load(f)
    for k,v in lan_claimers.items():
        claimers[k].append(v)

claimers = dict(claimers)

entID_merge = defaultdict(list)
for ents in claimers.values():
    for ent in ents:
        entID_merge[ent].extend(ents)
entID_merge = dict(entID_merge)

for k,v in entID_merge.items():
    entID_merge[k] = list(set(v))

for k,v in claimers.items():
    claimers[k] = entID_merge[v[0]]

new_option = []
for k,v in claimers.items():
    new_option.append({'Value':','.join(v), 'Label':k})

with open('claimers.json','w') as f:
    json.dump([{'Value':'None', 'Label':'All'}] + new_option,f,indent=4)

affiliation = []
objects = []
location = []
topic = []
for lan in ['en','es','ru']:
    dir_ = 'output_json_'+lan+'/' 

    with open(dir_+'claim_claimer_affiliation_counter.json','r') as f:
        affiliation += list(json.load(f).keys())
    with open(dir_+'claim_xvariable_counter.json','r') as f:
        objects += list(json.load(f).keys())
    with open(dir_+'claim_location_counter.json','r') as f:
        location += list(json.load(f).keys())
    with open(dir_+'claim_topic_counter.json','r') as f:
        topic += list(json.load(f).keys())

affiliation, objects, location, topic = list(set(affiliation)), list(set(objects)), list(set(location)), list(set(topic))

change_topic = []
for t in topic:
    if t == 'Non-Pharmaceutical Interventions (NPIs): Masks':
        change_topic.append('Wearing Masks')
    else:
        change_topic.append(t)
topic = change_topic

options = []
for option in [affiliation, objects, location, topic]:
    new_option = []
    for e in option:
        if e=="":
            new_option.append({'Value':"None", 'Label':"All"})
        else:
            new_option.append({'Value':e, 'Label':e})
    options.append(new_option)

new_topic = []
for e in topic:
    new_topic.append({'topic':e})


with open('affiliation.json','w') as f:
    json.dump([{'Value':'None', 'Label':'None'}]+options[0],f,indent=4)
with open('object.json','w') as f:
    json.dump([{'Value':'None', 'Label':'None'}]+options[1],f,indent=4)
with open('location.json','w') as f:
    json.dump([{'Value':'None', 'Label':'None'}]+options[2],f,indent=4)
with open('topic.json','w') as f:
    json.dump(new_topic,f,indent=4)
with open('topic_option.json','w') as f:
    json.dump([{'Value':'None', 'Label':'None'}]+options[3],f,indent=4)