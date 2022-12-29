import json
from tqdm import tqdm
from collections import defaultdict
from convert import run_conversion

def convert_outputs(token_data, event_data):
    events = defaultdict(list)
    for sentence, output in zip(token_data, event_data):
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


def append_events_to_oneie(oneie, events):
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


def convert(results, token_data, event_data):
    events = convert_outputs(token_data, event_data)
    json_data = results["oneie"]["en"]["json"]
    merged_data = {}
    for doc_id, doc_str in tqdm(json_data.items()):
        oneie = [json.loads(t) for t in doc_str.strip().split("\n")]
        if events is not None and doc_id in events:
            oneie = append_events_to_oneie(oneie, events[doc_id])
        json_str = ""
        for line in oneie:
            json_str += (json.dumps(line)+"\n")
        merged_data[doc_id] = json_str
    results["oneie"]["en"]["json"] = merged_data
    results = run_conversion(results, 'en')
    return results