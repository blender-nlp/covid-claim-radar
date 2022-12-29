import os 
import json 
import re 
from collections import defaultdict 
import argparse 
import glob 
from typing import List, Dict

import transformers 
from transformers import BartTokenizer
import torch 
from torch.utils.data import DataLoader 
import pytorch_lightning as pl

from .data import IEDataset, my_collate
from .utils import load_ontology

MAX_LENGTH=400
MAX_TGT_LENGTH=72

class CSDataModule(pl.LightningDataModule):
    '''
    Dataloader from Cold Start data format.
    This data module only has a TestDataloader.
    '''
    def __init__(self, args):
        super().__init__() 
        self.hparams = args 
        self.tokenizer = BartTokenizer.from_pretrained('facebook/bart-large')
        self.tokenizer.add_tokens([' <arg>',' <tgr>'])
    

    def create_gold_gen(self, template , context_words, trigger, mark_trigger=True):
        '''

        Input: <s> Template with special <arg> placeholders </s> </s> Passage </s>
        Output: <s> Template with arguments and <arg> when no argument is found. 
        '''
        # create input template 
        input_template = re.sub(r'<arg\d>', '<arg>', template) 
        space_tokenized_input_template = input_template.split()
        tokenized_input_template = [] 
        for w in space_tokenized_input_template:
            tokenized_input_template.extend(self.tokenizer.tokenize(w, add_prefix_space=True))
        

        # create context 
        if mark_trigger:
            prefix = self.tokenizer.tokenize(' '.join(context_words[:trigger['start']]), add_prefix_space=True) 
            tgt = self.tokenizer.tokenize(' '.join(context_words[trigger['start']: trigger['end']]), add_prefix_space=True)
            
            suffix = self.tokenizer.tokenize(' '.join(context_words[trigger['end']:]), add_prefix_space=True)
            context = prefix + [' <tgr>', ] + tgt + [' <tgr>', ] + suffix 
        else:
            context = self.tokenizer.tokenize(' '.join(context_words), add_prefix_space=True)

        
        # special case, tgt is empty 
        return tokenized_input_template, tokenized_input_template, context

    


            
    def prepare_data(self):
        data_dir = self.hparams.tmp_dir
        print('creating tmp dir ....')
        os.makedirs(data_dir, exist_ok=True)
        ontology_dict = load_ontology(ontology_file=self.hparams.ontology_file, ignore_case=True)
        # read events file 
        events = defaultdict(list) # doc_id to list of events 
        use_ins=True
        event_dict = {}
        with open(os.path.join(self.hparams.input_dir, 'cs/event.cs')) as f:
            for line in f:
                fields = line.strip().split('\t')
                if len(fields) == 0: continue 
                event_id = fields[0] # starts with :
                if fields[1] == 'type': # new event
                    # clean up last event 
                    if use_ins and event_dict:
                        events[event_dict['doc_id']].append(event_dict) 
                    use_ins=True
                    # new event 
                    evt_type = fields[2].split('#')[-1].replace('.Unspecified', '').replace('MHI.Disease.Disease','Life.Illness')
                    if evt_type not in ontology_dict: # should be a rare event type 
                        use_ins=False 
                        print(f'{evt_type} not found in ontology')
                        continue 
                    event_dict = {
                        'event_id': event_id,
                        'event_type': evt_type,
                        'doc_id': "",
                        'trigger': {},
                        'arguments': [] 
                    }
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
                    else: # arguments, actually don't need this for test time  
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
                        })
                    
            if use_ins and event_dict:
                events[event_dict['doc_id']].append(event_dict)
            
            # read documents 
            doc_dict = defaultdict(list) # doc_id -> list of sentences 
            for doc_path in glob.glob(os.path.join(self.hparams.input_dir, 'json/*.json')):
                doc_id = os.path.splitext(os.path.split(doc_path)[-1])[0] 
                
                with open(doc_path) as f:
                    for line in f:
                        sent = json.loads(line)
                        sent_id = sent['sent_id']
                        tokens = sent['tokens']
                        token_ids = sent['token_ids'] # same length as tokens 
                        doc_dict[doc_id].append(sent)
            # pair up triggers and contexts 
            # both events and sentences are sorted 
            

            def get_context(event_dict, doc_id, sent_idx, trigger=None):
                sents = doc_dict[doc_id]
                sent = sents[sent_idx]

                if not trigger: # assume the trigger is a single word 
                    token_idx = sent['token_ids'].index(event_dict['trigger']['position'])
                    trigger = {
                    'start': token_idx, 
                    'end': token_idx +1 
                    }
                else:
                    token_idx = trigger['start']
                offset = 0
                context_words = sent['tokens']
                if len(context_words) > MAX_LENGTH:
                    # cut it down 
                    context_words = context_words[token_idx-MAX_LENGTH//2 : token_idx+ MAX_LENGTH//2]
                    offset = max(0, token_idx-MAX_LENGTH//2)
                if sent_idx > 0 and len(context_words) + len(sents[sent_idx-1]['tokens']) <= MAX_LENGTH:
                    # use previous sentence
                    context_words = sents[sent_idx-1]['tokens'] + context_words 
                    offset -= len(sents[sent_idx-1]['tokens'])
                if sent_idx < len(sents)-1 and len(context_words) + len(sents[sent_idx+1]['tokens']) <= MAX_LENGTH:
                    # use next sentence as well 
                    context_words =  context_words + sents[sent_idx+1]['tokens']
                        
                trigger['start'] -= offset 
                trigger['end'] -= offset 
                template = ontology_dict[event_dict['event_type']]['template']
                input_template, output_template, context= self.create_gold_gen(
                    template,
                    context_words,
                    trigger,
                    self.hparams.mark_trigger)
                return input_template, output_template, context 
            
                        
            matched = [] 
            for doc_id in doc_dict:
                doc_events = events[doc_id]
                sents = doc_dict[doc_id]
                for event_dict in doc_events:
                    found = False 
                    for sent_idx, sent in enumerate(sents):
                        if event_dict['trigger']['position'] in sent['token_ids']: # this only works for single token triggers 
                            # found match 
                            found = True 
                            matched.append((event_dict,doc_id, sent_idx, None))
                    if not found:# multi-word trigger 
                        trigger = {} 
                        for sent_idx, sent in enumerate(sents):
                            for token_idx, position in enumerate(sent['token_ids']):
                                start_char = int(position.split(':')[1].split('-')[0])
                                end_char = int(position.split(':')[1].split('-')[1])
                                if start_char == event_dict['trigger']['char_start']:
                                    trigger['start'] = token_idx 
                                if end_char == event_dict['trigger']['char_end']:
                                    trigger['end'] = token_idx +1 
                                    if 'start' in trigger and 'end' in trigger:
                                        found= True 
                                        matched.append((event_dict, doc_id, sent_idx, trigger))
                                    break 
                            if found: break 
            
            writer = open(os.path.join(data_dir, 'test.jsonl'),'w') 
            for match in matched:
                event_dict,doc_id, sent_idx, trigger = match 
                input_template, output_template, context = get_context(event_dict, doc_id, sent_idx, trigger)
                input_tokens = self.tokenizer.encode_plus(input_template, context, 
                                    add_special_tokens=True,
                                    add_prefix_space=True,
                                    max_length=MAX_LENGTH,
                                    truncation='only_second',
                                    padding='max_length')
                            
                tgt_tokens = self.tokenizer.encode_plus(output_template, 
                add_special_tokens=True,
                add_prefix_space=True, 
                max_length=MAX_TGT_LENGTH,
                truncation=True,
                padding='max_length')

                processed_ex = {
                    'doc_key': event_dict['event_id'], 
                    'input_token_ids':input_tokens['input_ids'],
                    'input_attn_mask': input_tokens['attention_mask'],
                    'tgt_token_ids': tgt_tokens['input_ids'],
                    'tgt_attn_mask': tgt_tokens['attention_mask'],
                }
                writer.write(json.dumps(processed_ex) + '\n')
    
    def train_dataloader(self):
        return None 

    
    def val_dataloader(self):
        return None 

    def test_dataloader(self):
        if self.hparams.tmp_dir:
            data_dir = self.hparams.tmp_dir
        else:
            data_dir = 'preprocessed_{}'.format(self.hparams.dataset)

        dataset = IEDataset(os.path.join(data_dir, 'test.jsonl'))
        
        
        dataloader = DataLoader(dataset, pin_memory=True, num_workers=4, 
            collate_fn=my_collate, 
            batch_size=self.hparams.eval_batch_size, shuffle=False)

        return dataloader


if __name__ == '__main__':
    parser = argparse.ArgumentParser() 
    parser.add_argument('--input_dir', default='/home/zoey/projects/generative-ie/data/quizlet4/quizlet4_oneie_oct25/m1_m2')
    parser.add_argument('--tmp_dir', default='tmp')
    parser.add_argument('--train_batch_size', type=int, default=2)
    parser.add_argument('--eval_batch_size', type=int, default=4)
    parser.add_argument('--mark-trigger', action='store_true', default=True)
    parser.add_argument('--dataset', type=str, default='combined')
    args = parser.parse_args() 

    dm = CSDataModule(args=args)
    dm.prepare_data() 

    # training dataloader 
    dataloader = dm.test_dataloader() 

    for idx, batch in enumerate(dataloader):
        print(batch)
        break 

    # val dataloader 
