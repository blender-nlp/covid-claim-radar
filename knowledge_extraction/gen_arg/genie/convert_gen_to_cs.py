'''
Converts to Cold Start Format.
'''

import os 
import json 
import re 
import argparse 
from copy import deepcopy 
from collections import defaultdict
import glob
from typing import List, Dict, Any, Tuple 
import logging 

from genie.utils import load_ontology


def find_arg_span(arg: List[str], context_words: List[str], trigger_start: int, trigger_end: int):
    match = None 
    arg_len = len(arg)
    min_dis = len(context_words) # minimum distance to trigger 
    for i, w in enumerate(context_words):
        if context_words[i:i+arg_len] == arg:
            if i < trigger_start:
                dis = abs(trigger_start-i-arg_len)
            else:
                dis = abs(i-trigger_end)
            if dis< min_dis:
                match = (i, i+arg_len)
                min_dis = dis 
    
    return match 


def extract_args_from_template(evt_type, predicted, ontology_dict,):
    # extract argument text 
    template = ontology_dict[evt_type]['template']
    template_words = template.strip().split()
    predicted_words = predicted.strip().split()    
    predicted_args = {}
    t_ptr= 0
    p_ptr= 0 

    while t_ptr < len(template_words) and p_ptr < len(predicted_words):
        m = re.match(r'<(arg\d+)>', template_words[t_ptr])
        if m:
            arg_num = m.group(1)
            print(evt_type, arg_num)
            arg_name = ontology_dict[evt_type.replace('n/a','unspecified')][arg_num]
            
            if predicted_words[p_ptr] == '<arg>':
                # missing argument
                p_ptr +=1 
                t_ptr +=1  
            else:
                arg_start = p_ptr
                while (p_ptr < len(predicted_words)) and ((t_ptr+1 >= len(template_words)) or (predicted_words[p_ptr] != template_words[t_ptr+1])):
                    p_ptr+=1
                arg_text = predicted_words[arg_start:p_ptr]
                predicted_args[arg_name] = arg_text 
                t_ptr+=1 
                # aligned 
        else:
            t_ptr+=1 
            p_ptr+=1 
    print(predicted_args)
    return predicted_args


def load_entities(entity_file: str) -> Dict: 
    '''
    Read entities from entities.cs
    '''
    entities = {} # span -> entity 
    entity_dict = {}
    with open(entity_file) as f:
        for line in f:
            fields = line.strip().split('\t')
            entity_id = fields[0] 
            if len(fields) == 1: continue
            elif fields[1]=='type':# new entity 
                if 'position' in entity_dict:
                    entities[entity_dict['position']] = entity_dict
                entity_type = fields[2].split('#')[-1].replace('.Unspecified', '')
                entity_dict = {
                    'entity_id': entity_id,
                    'entity_type': entity_type,
                    'entity_name': "",
                    'position':"",
                }
            else:
                if fields[1] in ['mention', 'pronominal_mention', 'nominal_mention']:
                    mention_type = fields[1]
                    entity_name = fields[2]
                    position = fields[3]
                    entity_dict['entity_name'] = entity_name.strip('"')
                    entity_dict['position'] = position 
                    entity_dict['mention_type'] = mention_type
                    entities[entity_dict['position']] = {
                    'entity_id': entity_id,
                    'entity_type': entity_type,
                    'entity_name': entity_name.strip('"'),
                    'position': position,
                    'mention_type': mention_type
                    }
                elif fields[1] == 'canonical_mention':
                    entity_name = fields[2]
                    entity_dict['canonical_mention'] = entity_name.strip('"')
        
        if 'position' in entity_dict:
            entities[entity_dict['position']] = entity_dict 
        
    return entities 



def load_events(events_file: str, predicted: Dict, context: Dict, ontology_dict: Dict, entities: Dict)-> Dict[str, List]:
    events = defaultdict(list) # doc_id to list of events 
    use_ins=True
    event_dict = {}
    with open(events_file) as f:
        for line in f:
            fields = line.strip().split('\t')
            event_id = fields[0] # starts with :
            if fields[1]=='type':# new event
                # clean up last event 
                if use_ins and event_dict:
                    events[event_dict['doc_id']].append(event_dict) 
                use_ins=True
                # new event 
                evt_type = fields[2].split('#')[-1].replace('.Unspecified', '')
                if evt_type not in ontology_dict: # should be a rare event type 
                    use_ins=False 
                    print(f'{evt_type} not found in ontology, skipping..')
                    continue 
                event_dict = {
                    'event_id': event_id,
                    'event_type': evt_type,
                    'doc_id': "",
                    'trigger': {},
                    'arguments': [],
                    'new_arguments': [],
                }
                if event_id in predicted:
                    predicted_template = predicted[event_id]
                    
                    # get arguments 
                    predicted_args = extract_args_from_template(
                        evt_type, 
                        predicted_template, 
                        ontology_dict)
                    event_dict['predicted_args'] = predicted_args
                    event_dict['context'] = context[event_id]

            elif use_ins:
                if fields[1] == 'mention.actual': # trigger
                    text = fields[2]
                    position = fields[3] 
                    doc_id, char_span = position.split(':') 
                    char_start, char_end = [int(x) for x in char_span.split('-')] # this char index is inclusive 
                    event_dict['doc_id'] = doc_id 
                    event_dict['trigger'] = {
                        'text': text.strip('"'),
                        'char_start': char_start,
                        'char_end': char_end,
                        'position': position,
                    }

                elif fields[1] == 'canonical_mention.actual': # same as above 
                    continue 
                else: # arguments
                    role = fields[1].split('_')[-1].split('.')[0] 
                    entity_id = fields[2]
                    position=fields[3] 
                    if ':' not in position or '-' not in position: continue
                    doc_id, char_span = position.split(':') 
                    char_start, char_end = [int(x) for x in char_span.split('-')] # this char index is inclusive 
                    event_dict['arguments'].append({
                        'role': role,
                        'entity_id': entity_id,
                        'char_start': char_start, 
                        'char_end': char_end,
                        'position': position,
                        'text': entities[position]['entity_name'].strip('"')
                    })
                
        if use_ins and event_dict:
            events[event_dict['doc_id']].append(event_dict)
    
    return dict(events) 


def load_documents(doc_dir: str) -> Dict[str, List]:
    doc_dict = defaultdict(list) # doc_id -> list of sentences 
    for doc_path in glob.glob(os.path.join(doc_dir, '*.json')):
        doc_id = os.path.splitext(os.path.split(doc_path)[-1])[0] 
        
        with open(doc_path) as f:
            for line in f:
                sent = json.loads(line)
                sent_id = sent['sent_id']
                tokens = sent['tokens']
                token_ids = sent['token_ids'] # same length as tokens 
                doc_dict[doc_id].append(sent)

    return dict(doc_dict)  

def add_span(arg_span: Tuple[int, int], entity: List[str], 
        doc_id: str, event_dict: Dict, entity_n: int, entities: Dict, token_ids, argname)-> int:
    '''
    Align the extracted arguments with the detected entities or create new entities.
    `event_dict` and `entities` are updated in this process.
    '''
    # get char span 
    token_spans = token_ids[arg_span[0]: arg_span[1]]
    char_start = int(token_spans[0].split(':')[-1].split('-')[0])
    char_end = int(token_spans[-1].split(':')[-1].split('-')[1])
    position = '{}:{}-{}'.format(doc_id, char_start, char_end)
    if position in entities:
        # known entity span 
        entity_id = entities[position]['entity_id']
        mention_type = entities[position]['mention_type']
        event_dict['new_arguments'].append({
        'role': argname,
        'entity_id': entity_id,
        'char_start': int(char_start), 
        'char_end': int(char_end),
        'position': position,
        'text': ' '.join(entity),
        'mention_type': mention_type,
    })
    else:
        # find a partial match 
        token_spans = [token_ids[arg_span[1] -1] ] # take the last word 
        char_start = int(token_spans[0].split(':')[-1].split('-')[0])
        char_end = int(token_spans[-1].split(':')[-1].split('-')[1])
        position = '{}:{}-{}'.format(doc_id, char_start, char_end)
        if position in entities:
            entity_id = entities[position]['entity_id']
            mention_type = entities[position]['mention_type']
            event_dict['new_arguments'].append({
                'role': argname,
                'entity_id': entity_id,
                'char_start': int(char_start), 
                'char_end': int(char_end),
                'position': position,
                'text': ' '.join(entity),
                'mention_type': mention_type,
            })
        else:
            # new entity 
            entity_n +=1 
            entity_id = ':Entity_EDL_ARG_{:07d}'.format(entity_n)
            print('adding unseen entity {} {}'.format(entity_id, entity))
            entities[position] = {
                'entity_type': 'COM',
                'entity_name': ' '.join(entity),
                'entity_id': entity_id,
                'position': position,
                'mention_type': 'nominal_mention' # TODO: rules for deciding the mention type 
            }
            # add new entity as argument 
            event_dict['new_arguments'].append({
                'role': argname,
                'entity_id': entity_id,
                'char_start': int(char_start), 
                'char_end': int(char_end),
                'position': position,
                'text': ' '.join(entity),
                'mention_type': 'nominal_mention'
            })
    
    return entity_n



def dump_entities(entity_file: str, new_entities: Dict):
    '''
    :params entities: Dict, entity position -> dict
    '''
    entity_by_id =[]
    for ent_pos, ent_dict in new_entities.items():
        entity_by_id.append((ent_dict['entity_id'], ent_dict))
    
    sorted_entities = sorted(entity_by_id, key=lambda x: x[0])
    cs_writer = open(entity_file, 'w+')
    '''
    :Entity_EDL_0000001	type	PER	1.0000
    :Entity_EDL_0000001	canonical_mention	"we"	L0C04CVVW:63-64	1.0000
    :Entity_EDL_0000001	pronominal_mention	"we"	L0C04CVVW:63-64	1.0000
    '''
    for ent_id, ent_dict in sorted_entities:
        cs_writer.write(f"{ent_id}\ttype\t{ent_dict['entity_type']}\t1.0000\n")
        cs_writer.write(f'{ent_id}\tcanonical_mention\t"{ent_dict["entity_name"]}"\t{ent_dict["position"]}\t1.0000\n')
        cs_writer.write(f'{ent_id}\t{ent_dict["mention_type"]}\t"{ent_dict["entity_name"]}"\t{ent_dict["position"]}\t1.0000\n')
    
    cs_writer.close() 
    return 



def merge_arguments(args):
    ontology_dict = load_ontology(ontology_file=args.ontology_file, ignore_case=True)

    # read predictions from model 
    predicted = {} # event_id -> predicted 
    context = {} # event_id -> input 
    with open(args.gen_file) as f:
        for line in f:
            gen_ex = json.loads(line)
            event_id = gen_ex['doc_key']
            predicted[event_id] = gen_ex['predicted']
            context[event_id] = gen_ex['input']
    
   
    
    entities = load_entities(os.path.join(args.input_dir, 'cs/entity.cs'))
    old_entities= deepcopy(entities)
    entity_n = len(entities)

    # read events file and combine 
    events = load_events(os.path.join(args.input_dir, 'cs/event.cs'), predicted, context, ontology_dict, entities)
    # read documents 
    doc_dict = load_documents(os.path.join(args.input_dir, 'json'))
    # pair up triggers and contexts 
    # both events and sentences are sorted 
    total_args = 0
    found_args = 0
    for doc_id in doc_dict:
        if doc_id in events:
            doc_events = events[doc_id]
            sents = doc_dict[doc_id]
            for event_dict in doc_events:
                for sent_idx, sent in enumerate(sents):
                    if event_dict['trigger']['position'] in sent['token_ids']: # this only works for single token triggers 
                        # found match 
                        offset= 0
                        token_idx = sent['token_ids'].index(event_dict['trigger']['position'])
                        context_words = sent['tokens']
                        token_ids = sent['token_ids']

                        if sent_idx > 0:
                            context_words = sents[sent_idx-1]['tokens'] + context_words
                            token_ids = sents[sent_idx-1]['token_ids'] + token_ids 
                            offset -= len(sents[sent_idx-1]['tokens'])
                        if sent_idx < len(sents) -1:
                            context_words =  context_words + sents[sent_idx+1]['tokens']
                            token_ids = token_ids + sents[sent_idx+1]['token_ids']
                        # get the word offset for the trigger 
                        trigger = {
                                    'start': token_idx - offset, 
                                    'end': token_idx-offset +1
                                }
                        for argname in event_dict['predicted_args']:
                            total_args +=1 
                            entity = event_dict['predicted_args'][argname]# this argument span is inclusive 
                            if len(entity) == 0:
                                continue 
                            arg_span = find_arg_span(entity, context_words, 
                                trigger['start'], trigger['end']) 
                            if arg_span:# if None means hullucination
                                # indexes are word level 
                                found_args +=1 
                                entity_n = add_span(arg_span, entity, doc_id, event_dict, entity_n, entities, token_ids, argname)
                            else:
                                # try to break down the argument into multiple args 
                                new_entity = []
                                for w in entity:
                                    if w == 'and' and len(new_entity) >0:
                                        arg_span = find_arg_span(new_entity, context_words, trigger['start'], trigger['end'])
                                        if arg_span:  
                                            entity_n = add_span(arg_span, new_entity, doc_id, event_dict,entity_n, entities, token_ids, argname)
                                            found_args +=1 
                                        new_entity = []
                                    else:
                                        new_entity.append(w)
                                
                                if len(new_entity) >0: # last entity
                                    arg_span = find_arg_span(new_entity, context_words, trigger['start'], trigger['end'])
                                    if arg_span:  
                                        entity_n = add_span(arg_span, new_entity, doc_id, event_dict,entity_n, entities, token_ids, argname)
                                        found_args +=1 
                            
    print('{} total new argument spans'.format(total_args))
    print('{} arguments matched to entities'.format(found_args))

    # save entities to file 
    new_entities = {} 
    for key in entities:
        if key not in old_entities:
            new_entities[key] = entities[key]

    dump_entities(os.path.join(args.input_dir, 'cs/entity.aug.cs'), new_entities)


    # merge arguments, resolve conflicts and write to file 
    writer = open(args.merged_file,'w')
    diff_writer = open(args.diff_file,'w')
    diff_events = []
    all_events = []

    for doc_id in doc_dict:
        if doc_id in events:
            doc_events = events[doc_id]
            for event_dict in doc_events:
                all_events.append(event_dict)

    all_events = sorted(all_events, key=lambda x:x['event_id'])

    new_role_arg_n = 0
    conflict_arg_n =0 
    old_arg_n =0 
    new_arg_n =0 
    cs_writer = open(os.path.join(args.input_dir, 'cs/event.aug.cs'), 'w') 
    for event_dict in all_events:
        keep_diff =False 
        event_dict['merged_arguments'] = []
        old_arguments = defaultdict(list) # role -> list of entity id 
        old_arg_n += len(event_dict['arguments'])

        for arg in event_dict['arguments']:
            event_dict['merged_arguments'].append(arg)
            old_arguments[arg['role']].append((arg['entity_id'], arg['text']))
        
        new_arg_n += len(event_dict['new_arguments'])
        for arg in event_dict['new_arguments']:
            if arg['role'] not in old_arguments:
                event_dict['merged_arguments'].append(arg)
                new_role_arg_n +=1 
                keep_diff= True 
            else:
                seen = False
                for ent_id, text in old_arguments[arg['role']]:
                    if ent_id == arg['entity_id'] or text == arg['text']:
                        seen= True 
                        break 
                if not seen:
                    # if the new argument is not a pronoun, add it back 
                    if arg['mention_type']!='pronominal_mention':
                        event_dict['merged_arguments'].append(arg)
                    # print('conflicting args for event {} role {}'.format(event_dict['trigger']['text'], arg['role']))
                    # old_text = ','.join([tup[1] for tup in old_arguments[arg['role']]])
                    # print('old: {}, new: {}'.format(old_text, arg['text']))
                    conflict_arg_n +=1 
                    keep_diff = True 
        
        # write to cs format 
        #:Event_000001	type	Justice.ArrestJailDetain.Unspecified	1.0000
        #:Event_000001	mention.actual	"Arrested"	K0C047Z57:11-18	1.0000
        #:Event_000001	canonical_mention.actual	"Arrested"	K0C047Z57:11-18	1.0000
        #:Event_000001	Justice.ArrestJailDetain.Unspecified_Detainee.actual	:Entity_EDL_0000002	K0C047Z57:6-9	0.8847
        cs_writer.write('{}\ttype\t{}\t1.0000\n'.format(event_dict['event_id'],event_dict['event_type']))
        cs_writer.write('{}\tmention.actual\t"{}"\t{}\t1.0000\n'.format(
            event_dict['event_id'], 
            event_dict['trigger']['text'],
            event_dict['trigger']['position']
        ))
        cs_writer.write('{}\tcanonical_mention.actual\t"{}"\t{}\t1.0000\n'.format(
            event_dict['event_id'], 
            event_dict['trigger']['text'],
            event_dict['trigger']['position']
        ))
        for arg in event_dict['merged_arguments']:
            cs_writer.write('{}\t{}_{}.actual\t{}\t{}\t1.0000\n'.format(
                event_dict['event_id'], 
                event_dict['event_type'],
                arg['role'],
                arg['entity_id'],
                arg['position']
            ))
        
        if keep_diff:
            diff_events.append(event_dict)
        
        writer.write(json.dumps(event_dict) +'\n')
    
    cs_writer.close() 
    writer.close() 

    print('{} total original arguments'.format(old_arg_n))
    print('{} arguments fill in new roles'.format(new_role_arg_n))
    print('{} conflicting arguments '.format(conflict_arg_n))

    diff_writer.write(json.dumps(diff_events, indent=2))



if __name__ == '__main__':
    parser = argparse.ArgumentParser() 
    parser.add_argument('--gen_file',type=str, default='checkpoints/test_weaksup-pred/predictions.jsonl')
    parser.add_argument('--input_dir',type=str, default='data/weak')
    parser.add_argument('--merged_file',type=str,default='checkpoints/test_weaksup-pred/merged.jsonl')
    parser.add_argument('--diff_file',type=str, default='checkpoints/test_weaksup-pred/diff.json')
    parser.add_argument('--ontology_file', type=str, default='event_role_KAIROS_P2.json')
    args = parser.parse_args() 


    merge_arguments(args)


    
