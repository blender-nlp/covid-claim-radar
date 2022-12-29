import json
from tqdm import tqdm
from collections import defaultdict
import glob
import os

import argparse


INPUT_DIR = "./input"
INPUT_TYPE = ["doc", "combined"][0]
RESOURCE_DIR = "./resources/models/covid"
OUTPUT_DIR = "./output"

ENTITY_TYPE_MAPPING = {
    'URL': 'URL',
    'TME': 'Time',
    'TTL': 'Title',
    'MON': 'Money',
    'PER': 'Person',
    'WEA': 'Weapon',
    'VEH': 'Vehicle',
    'LOC': 'Location',
    'FAC': 'Facility',
    'ORG': 'Organization',
    'VAL': 'NumericalValue',
    'GPE': 'GeopoliticalEntity',
    'CRM': 'Crime',
    'LAW': 'Law',
    'BAL': 'Ballot',
    'COM': 'Commodity',
    'SID': 'Sides'
}
ENTITY_MENTION_TYPE_MAPPING = {
    "mention": "NAM",
    "nominal_mention": "NOM",
    "pronominal_mention": "PRO"
}

parser = argparse.ArgumentParser()
parser.add_argument("--input_dir", "-i", type=str, default=INPUT_DIR)
parser.add_argument("--output_dir", "-o", type=str, default=OUTPUT_DIR)
parser.add_argument("--input_type", "-t", type=str, default=INPUT_TYPE)
parser.add_argument("--merged_ent_cs", "-m", type=str, default=os.path.join(OUTPUT_DIR, "merged_fine.cs"))
parser.add_argument("--resource_dir", "-r", type=str, default=RESOURCE_DIR)
parser.add_argument("--no_add_contents", "-n", action='store_true')

args = parser.parse_args()
def convert_outputs(processed_jsonl, output_jsonl):
    events = defaultdict(list)
    with open(processed_jsonl, "rt") as fp:
        token_data = [json.loads(t) for t in fp]
    if os.path.exists(output_jsonl):
        with open(output_jsonl, "rt") as fp:
            outputs = [json.loads(t) for t in fp]
        for sentence, output in zip(token_data, outputs):
            prefix_space = sentence['sentence'].index(sentence['tokens'][0])
            sent_start = sentence['token_offsets'][0][0] - prefix_space
            doc_id = '-'.join(sentence["sent_id"].split('-')[:-1])
            for event in output['events']:
                converted_event = {
                    "doc_id": doc_id,
                    "trigger": [event['trigger'][0] + sent_start, event['trigger'][1] + sent_start - 1, event["trigger"][2]],
                    "arguments": [
                        [argument[0][0] + sent_start, argument[0][1] + sent_start - 1, argument[1]] for argument in event["arguments"]
                    ]
                }
                events[doc_id].append(converted_event)
    else:
        # no argument results
        for sentence in token_data:
            prefix_space = sentence['sentence'].index(sentence['tokens'][0])
            sent_start = sentence['token_offsets'][0][0] - prefix_space
            doc_id = '-'.join(sentence["sent_id"].split('-')[:-1])
            for event in output['events']:
                converted_event = {
                    "doc_id": doc_id,
                    "trigger": [event['trigger'][0] + sent_start, event['trigger'][1] + sent_start - 1, event["trigger"][2]],
                    "arguments": [
                        [argument[0][0] + sent_start, argument[0][1] + sent_start - 1, argument[1]] for argument in event["arguments"]
                    ]
                }
                events[doc_id].append(converted_event)
    for doc in events:
        events[doc].sort(key=lambda t:t['trigger'][0])
    return events


def convert_cs_entities(cs_file):
    entities = defaultdict(list)
    with open(cs_file) as fp:
        current_ent_type = None
        for line in fp:
            if not line.startswith(":Entity_EDL_"):
                continue
            elements = line.split("\t")
            if elements[1] == "type":
                current_ent_type = elements[2].split('/')[-1].split('#')[-1]
                if current_ent_type in ENTITY_TYPE_MAPPING:
                    current_ent_type = ENTITY_TYPE_MAPPING[current_ent_type]
            elif elements[1] in ENTITY_MENTION_TYPE_MAPPING:
                mention_type = ENTITY_MENTION_TYPE_MAPPING[elements[1]]
                doc_id = elements[3].split(":")[0]
                offsets = _token_offset_from_str(elements[3])
                entities[doc_id].append([offsets[0], offsets[1], current_ent_type, mention_type, elements[4]])
    for doc_id in entities:
        entities[doc_id].sort(key=lambda key:key[0])
    return entities


def find_token_offsets(token_offsets, char_start, char_end):
    i = 0
    if token_offsets[-1][1] < char_end or token_offsets[0][0] > char_start:
        return -1, -1
    while i < len(token_offsets) and token_offsets[i][0] <= char_start:
        i += 1
    ms = i - 1
    j = len(token_offsets) - 1
    while j >= 0 and token_offsets[j][1] > char_end:
        j -= 1
    mt = j + 1
    if ms >= mt:
        mt = ms + 1
    return ms, mt


def _token_offset_from_str(token_str):
    offset = token_str.split(':')[1].split('-')
    return int(offset[0]), int(offset[1])


def append_events_to_oneie(oneie_file_or_data, events):
    if isinstance(oneie_file_or_data, str):
        with open(oneie_file_or_data, "rt") as fp:
            oneie = [json.loads(t) for t in fp]
    else:
        oneie = oneie_file_or_data
    event_idx = 0
    for sentence in oneie:
        if event_idx == len(events):
            break
        token_offsets = [_token_offset_from_str(t) for t in sentence['token_ids']]
        entity_offset_id = {(t[0], t[1]): i for i, t in enumerate(sentence['graph']['entities'])}
        n_oldevent = len(sentence['graph']['triggers'])
        trigger_offset = find_token_offsets(token_offsets, events[event_idx]['trigger'][0], events[event_idx]['trigger'][1])
        n_new = 0
        while trigger_offset[0] != -1:
            sentence['graph']['triggers'].append([trigger_offset[0], trigger_offset[1], events[event_idx]['trigger'][2], 1.0])
            for argument in events[event_idx]['arguments']:
                arg_start, arg_end, role_type = argument
                token_start, token_end = find_token_offsets(token_offsets, arg_start, arg_end)
                if (token_start, token_end) in entity_offset_id:
                    sentence['graph']['roles'].append([n_oldevent+n_new, entity_offset_id[(token_start, token_end)], role_type, 1.0])
            n_new += 1
            event_idx += 1
            if event_idx == len(events):
                break
            trigger_offset = find_token_offsets(token_offsets, events[event_idx]['trigger'][0], events[event_idx]['trigger'][1])
    return oneie


def add_entities_to_oneie(oneie_file_or_data, entities):
    if isinstance(oneie_file_or_data, str):
        with open(oneie_file_or_data, "rt") as fp:
            oneie = [json.loads(t) for t in fp]
    else:
        oneie = oneie_file_or_data
    entity_idx = 0
    for sentence in oneie:
        if entity_idx == len(entities):
            break
        token_offsets = [_token_offset_from_str(t) for t in sentence['token_ids']]
        entity_offset_id = {(t[0], t[1]): i for i, t in enumerate(sentence['graph']['entities'])}
        new_entity_offset = find_token_offsets(token_offsets, entities[entity_idx][0], entities[entity_idx][1])
        while new_entity_offset[0] != -1:
            if new_entity_offset in entity_offset_id:
                if sentence['graph']['entities'][entity_offset_id[new_entity_offset]][2] != entities[entity_idx][2]:
                    sentence['graph']['entities'][entity_offset_id[new_entity_offset]][2] = entities[entity_idx][2]
                    sentence['graph']['entities'][entity_offset_id[new_entity_offset]][3] = entities[entity_idx][3]
                    sentence['graph']['entities'][entity_offset_id[new_entity_offset]][4] = entities[entity_idx][4]
            else:
                sentence['graph']['entities'].append(list(new_entity_offset) + entities[entity_idx][2:])
            entity_idx += 1
            if entity_idx == len(entities):
                break
            new_entity_offset = find_token_offsets(token_offsets, entities[entity_idx][0], entities[entity_idx][1])
    return oneie


def _makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

if not args.no_add_contents:
    if os.path.exists(args.merged_ent_cs):
        entities = convert_cs_entities(args.merged_ent_cs)
    else:
        entities = None
    if os.path.exists(os.path.join(args.output_dir, "docs.jsonl")):
        events = convert_outputs(os.path.join(args.output_dir,"docs.jsonl"), os.path.join(args.output_dir, "docs.args.jsonl"))
    else:
        events = None
else:
    entities = events = None

_makedirs(os.path.join(args.output_dir, "json"))
_makedirs(os.path.join(args.output_dir, "mention"))
_makedirs(os.path.join(args.output_dir, "cs"))
if args.input_type == 'doc':
    oneie_files = glob.glob(os.path.join(args.input_dir, "*.json"))
    for oneie_file in tqdm(oneie_files):
        doc_id = os.path.split(oneie_file)[1].split(".")[0]
        oneie = None
        if entities is not None and doc_id in entities:
            oneie = add_entities_to_oneie(oneie_file, entities[doc_id])
        if events is not None and doc_id in events:
            oneie = append_events_to_oneie(oneie if oneie else oneie_file, events[doc_id])
        if oneie is None:
            os.system(f"cp {oneie_file} {os.path.join(args.output_dir, 'json', doc_id+'.json')}")
        else:
            with open(os.path.join(args.output_dir, f"json/{doc_id}.json"), "wt") as fp:
                for line in oneie:
                    fp.write(json.dumps(line)+"\n")
elif args.input_type == 'combined':
    json_file = os.path.join(args.input_dir, "oneie.json")
    with open(json_file) as fp:
        all_data = json.load(fp)
    json_data = all_data["oneie"]["en"]["json"]
    for doc_id, doc_str in tqdm(json_data.items()):
        oneie = [json.loads(t) for t in doc_str.strip().split("\n")]
        if entities is not None and doc_id in entities:
            oneie = add_entities_to_oneie(oneie, entities)
        if events is not None and doc_id in events:
            oneie = append_events_to_oneie(oneie, events[doc_id])
        with open(os.path.join(args.output_dir, f"json/{doc_id}.json"), "wt") as fp:
            for line in oneie:
                fp.write(json.dumps(line)+"\n")
