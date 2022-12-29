import os
import glob
import json
from copy import deepcopy
from collections import defaultdict

cur_dir = os.path.dirname(os.path.realpath(__file__))

entity_type_mapping = {
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

entity_type_rev_mapping = {v: k for k, v in entity_type_mapping.items()}

entity_type_mapping_file = os.path.join(cur_dir, 'resource', 'ace_to_aida_entity.tsv')
event_type_mapping_file = os.path.join(cur_dir, 'resource', 'ace_to_aida_event.tsv')
role_type_mapping_file = os.path.join(cur_dir, 'resource', 'ace_to_aida_role.tsv')
relation_type_mapping_file = os.path.join(cur_dir, 'resource', 'ace_to_aida_relation.tsv')

PREFIX = 'https://tac.nist.gov/tracks/SM-KBP/2018/ontologies/SeedlingOntology#'
# AIDA_PREFIX = 'https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntologyM36#'
AIDA_PREFIX = '' #'https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#'

def load_mapping(mapping_file):
    mapping = {}
    with open(mapping_file, 'r', encoding='utf-8') as r:
        for line in r:
            from_type, to_type = line.strip().split('\t')
            mapping[from_type] = to_type
    return mapping


def get_span_mention_text(tokens, token_ids, start, end):
    if start + 1 == end:
        return tokens[start], token_ids[start]

    if end > len(tokens):
        print(tokens, token_ids, start, end)
    if start >= len(tokens):
        print(token_ids, tokens, start, end)
        input()
    start_token = tokens[start]
    end_token = tokens[end - 1]
    start_char = int(token_ids[start].split(':')[1].split('-')[0])
    end_char = int(token_ids[end - 1].split(':')[1].split('-')[1])
    text = ' ' * (end_char - start_char + 1)
    for token, token_id in zip(tokens[start:end], token_ids[start:end]):
        token_start, token_end = token_id.split(':')[1].split('-')
        token_start, token_end = int(token_start), int(token_end)
        token_start -= start_char
        token_end -= start_char
        assert len(text[:token_start] + token + text[token_end + 1:]) == len(text)
        text = text[:token_start] + token + text[token_end + 1:]
    return text, '{}:{}-{}'.format(token_ids[start].split(':')[0],
                                   start_char, end_char)


def json_to_cs_fg(input_dir, output_dir):
    json_files = glob.glob(os.path.join(input_dir, '*.json'))
    # convert entities
    print('Converting entity mentions and generate entity cs file')
    entity_mapping = {}
    entity_id_mapping = {}
    entity_cs_file = os.path.join(output_dir, 'entity.cs')
    with open(entity_cs_file, 'w', encoding='utf-8') as w:
        for f in json_files:
            with open(f, 'r', encoding='utf-8') as r:
                for line in r:
                    result = json.loads(line)
                    doc_id = result['doc_id']
                    sent_id = result['sent_id']
                    tokens, token_ids = result['tokens'], result['token_ids']
                    for i, (start, end, enttype, mentype, entscore) in enumerate(result['graph']['entities']):
                        entity_text, entity_span = get_span_mention_text(
                            tokens, token_ids, start, end)
                        entity_text = entity_text.replace('\n', ' ').replace('\t', ' ')
                        entity_id = 'Entity_EDL_{:07d}'.format(len(entity_mapping) + 1)
                        # enttype = PREFIX + enttype
                        entity_mapping[(sent_id, i)] = (entity_text, entity_id, entity_span, enttype, mentype)
                        entity_id_mapping[entity_id] = (sent_id, i)
                        # enttype_mapped = entity_type_mapping[enttype]
                        w.write(':{}\ttype\t{}\t{:.4f}\n'.format(entity_id, enttype, entscore))
                        w.write(':{}\tcanonical_mention\t"{}"\t{}\t{:.4f}\n'.format(
                            entity_id, entity_text, entity_span, entscore))
                        mention = ('mention' if mentype == 'NAM'
                                   else 'nominal_mention' if mentype == 'NOM'
                                   else 'pronominal_mention' if mentype == 'PRO'
                                   else 'UNK')
                        w.write(':{}\t{}\t"{}"\t{}\t{:.4f}\n'.format(
                            entity_id, mention, entity_text, entity_span, entscore))
                        # skip the link line

    # converting relations and events
    print('Converting relations and events')
    event_count = 0
    relation_cs_file = os.path.join(output_dir, 'relation.cs')
    event_cs_file = os.path.join(output_dir, 'event.cs')
    with open(relation_cs_file, 'w', encoding='utf-8') as rel_w, \
        open(event_cs_file, 'w', encoding='utf-8') as evt_w:
        for f in json_files:
            with open(f, 'r', encoding='utf-8') as r:
                for line in r:
                    result = json.loads(line)
                    sent_id = result['sent_id']
                    tokens, token_ids = result['tokens'], result['token_ids']
                    relations = result['graph']['relations']
                    triggers = result['graph']['triggers']
                    roles = result['graph']['roles']
                    # sentence span
                    sent_span = '{}:{}-{}'.format(
                        token_ids[0].split(':')[0],
                        token_ids[0].split(':')[1].split('-')[0],
                        token_ids[-1].split(':')[1].split('-')[1])
                    # convert relations
                    for rel_item in relations:
                        arg1, arg2, _, relscore, reltype = rel_item
                        entity_id_1 = entity_mapping[(sent_id, arg1)][1]
                        entity_id_2 = entity_mapping[(sent_id, arg2)][1]
                        # reltype = PREFIX + reltype
                        rel_w.write(':{}\t{}\t:{}\t{}\t{:.4f}\n'.format(
                            entity_id_1, reltype, entity_id_2, sent_span, relscore
                        ))
                    # convert events
                    for cur_trigger_idx, (start, end, eventtype, eventscore) in enumerate(triggers):
                        event_count += 1
                        event_id = 'Event_{:06d}'.format(event_count)
                        trigger_text, trigger_span = get_span_mention_text(
                            tokens, token_ids, start, end)
                        trigger_text.replace('\n', ' ').replace('\t', ' ')
                        # eventtype = PREFIX + eventtype
                        # eventtype_mapped = event_type_mapping[eventtype]
                        evt_w.write(':{}\ttype\t{}\t{:.4f}\n'.format(event_id, eventtype, eventscore))
                        evt_w.write(':{}\tmention.actual\t"{}"\t{}\t{:.4f}\n'.format(
                            event_id, trigger_text, trigger_span, eventscore))
                        evt_w.write(':{}\tcanonical_mention.actual\t"{}"\t{}\t{:.4f}\n'.format(
                            event_id, trigger_text, trigger_span, eventscore))
                        for trigger_idx, entity_idx, role, rolescore in roles:
                            if cur_trigger_idx == trigger_idx:
                                # role_mapped = role_type_mapping['{}:{}'.format(eventtype, role).lower()]
                                role = '{}_{}'.format(eventtype, role)
                                _, entity_id, entity_span, _, _ = entity_mapping[(sent_id, entity_idx)]
                                evt_w.write(':{}\t{}.actual\t:{}\t{}\t{:.4f}\n'.format(
                                    event_id, role, entity_id, entity_span, rolescore))


def json_to_cs_aida(input_dir, output_dir):
    json_files = glob.glob(os.path.join(input_dir, '*.json'))
    # convert entities
    print('Converting entity mentions and generate entity cs file')
    entity_mapping = {}
    entity_id_mapping = {}
    entity_cs_file = os.path.join(output_dir, 'entity.cs')
    with open(entity_cs_file, 'w', encoding='utf-8') as w:
        for f in json_files:
            with open(f, 'r', encoding='utf-8') as r:
                for line in r:
                    result = json.loads(line)
                    doc_id = result['doc_id']
                    sent_id = result['sent_id']
                    tokens, token_ids = result['tokens'], result['token_ids']
                    for i, (start, end, enttype, mentype, _) in enumerate(result['graph']['entities']):
                        entity_text, entity_span = get_span_mention_text(
                            tokens, token_ids, start, end)
                        entity_id = 'Entity_EDL_{:07d}'.format(len(entity_mapping) + 1)
                        enttype = entity_type_rev_mapping[enttype] if enttype in entity_type_rev_mapping else enttype
                        enttype = AIDA_PREFIX + enttype
                        entity_mapping[(sent_id, i)] = (entity_text, entity_id, entity_span, enttype, mentype)
                        entity_id_mapping[entity_id] = (sent_id, i)
                        w.write(':{}\ttype\t{}\t1.000000\n'.format(entity_id, enttype))
                        w.write(':{}\tcanonical_mention\t"{}"\t{}\t0.000\n'.format(
                            entity_id, entity_text, entity_span))
                        mention = ('mention' if mentype == 'NAM'
                                   else 'nominal_mention' if mentype == 'NOM'
                                   else 'pronominal_mention' if mentype == 'PRO'
                                   else 'UNK')
                        w.write(':{}\t{}\t"{}"\t{}\t0.000\n'.format(
                            entity_id, mention, entity_text, entity_span))
                        # skip the link line

    # converting relations and events
    print('Converting relations and events')
    event_count = 0
    relation_cs_file = os.path.join(output_dir, 'relation.cs')
    event_cs_file = os.path.join(output_dir, 'event.cs')
    with open(relation_cs_file, 'w', encoding='utf-8') as rel_w, \
        open(event_cs_file, 'w', encoding='utf-8') as evt_w:
        for f in json_files:
            with open(f, 'r', encoding='utf-8') as r:
                for line in r:
                    result = json.loads(line)
                    sent_id = result['sent_id']
                    tokens, token_ids = result['tokens'], result['token_ids']
                    relations = result['graph']['relations']
                    triggers = result['graph']['triggers']
                    roles = result['graph']['roles']
                    # sentence span
                    sent_span = '{}:{}-{}'.format(
                        token_ids[0].split(':')[0],
                        token_ids[0].split(':')[1].split('-')[0],
                        token_ids[-1].split(':')[1].split('-')[1])
                    # convert relations
                    for rel_item in relations:
                        arg1, arg2, _, _, reltype = rel_item
                        entity_id_1 = entity_mapping[(sent_id, arg1)][1]
                        entity_id_2 = entity_mapping[(sent_id, arg2)][1]
                        reltype = AIDA_PREFIX + reltype
                        rel_w.write(':{}\t{}\t:{}\t{}\t1.000\n'.format(
                            entity_id_1, reltype, entity_id_2, sent_span
                        ))
                    # convert events
                    for cur_trigger_idx, (start, end, eventtype, _) in enumerate(triggers):
                        event_count += 1
                        event_id = 'Event_{:06d}'.format(event_count)
                        trigger_text, trigger_span = get_span_mention_text(
                            tokens, token_ids, start, end)
                        eventtype = AIDA_PREFIX + eventtype
                        # eventtype_mapped = event_type_mapping[eventtype]
                        evt_w.write(':{}\ttype\t{}\n'.format(event_id, eventtype))
                        evt_w.write(':{}\tmention.actual\t"{}"\t{}\t1.000\n'.format(
                            event_id, trigger_text, trigger_span))
                        evt_w.write(':{}\tcanonical_mention.actual\t"{}"\t{}\t1.000\n'.format(
                            event_id, trigger_text, trigger_span))
                        for trigger_idx, entity_idx, role, _ in roles:
                            if cur_trigger_idx == trigger_idx:
                                # role_mapped = role_type_mapping['{}:{}'.format(eventtype, role).lower()]
                                role = '{}_{}'.format(eventtype, role)
                                _, entity_id, entity_span, _, _ = entity_mapping[(sent_id, entity_idx)]
                                evt_w.write(':{}\t{}.actual\t:{}\t{}\t1.000\n'.format(
                                    event_id, role, entity_id, entity_span))


def mention_to_tab(start, end, entity_type, mention_type, mention_id, tokens,
                   token_ids, score=1, rev_entity_type=True):
    if start >= end:
        print(tokens, start, end)
        return ''
    tokens = tokens[start:end]
    token_ids = token_ids[start:end]
    span = '{}:{}-{}'.format(token_ids[0].split(':')[0],
                             token_ids[0].split(':')[1].split('-')[0],
                             token_ids[-1].split(':')[1].split('-')[1])
    mention_text = tokens[0]
    previous_end = int(token_ids[0].split(':')[1].split('-')[1])
    for token, token_id in zip(tokens[1:], token_ids[1:]):
        start, end = token_id.split(':')[1].split('-')
        start, end = int(start), int(end)
        mention_text += ' ' * (start - previous_end - 1) + token
        previous_end = end
    if rev_entity_type:
        entity_type = entity_type_rev_mapping.get(entity_type, entity_type)
    return '\t'.join([
        'json2tab',
        mention_id,
        mention_text,
        span,
        'NIL',
        entity_type,
        mention_type,
        '1.0' if score == 1 else '{:.4f}'.format(score)
    ])


def convert_sent(sent, token_col=0, span_col=1, label_col=-1):
    mentions = []
    mention = []
    for idx, line in enumerate(sent):
        token, span, label = line[token_col], line[span_col], line[label_col]
        if label == 'O':
            if mention:
                mentions.append(mention)
                mention = []
        else:
            doc_id, offsets = span.split(':')
            start, end = offsets.split('-')
            start, end = int(start), int(end)
            if label.startswith('B-'):
                if mention:
                    mentions.append(mention)
                    mention = []
            mention.append((token, doc_id, start, end, idx))
    if mention:
        mentions.append(mention)

    if len(mentions) == 0:
        return None

    annotations = []
    for mention in mentions:
        text = ' '.join([t[0] for t in mention])
        mention_id = '{}:{}-{}'.format(mention[0][1],      # doc_id
                                       mention[0][2],      # start offset
                                       mention[-1][3],     # end offset
                                       )
        start, end = mention[0][-1], mention[-1][-1] + 1
        annotations.append({
            'mention': text,
            'mention_id': mention_id,
            'start': start,
            'end': end
        })
    tokens = [t[token_col] for t in sent]
    return {
        'tokens': tokens,
        'annotations': annotations
    }


def bio_to_cfet(input_file, output_file,
            token_col=0, span_col=1, label_col=-1, separator=' '):
    with open(input_file, 'r', encoding='utf-8') as r, \
            open(output_file, 'w', encoding='utf-8') as w:
        sent = []
        for line in r:
            line = line.rstrip('\n')
            if line:
                sent.append(line.split(separator))
            else:
                if sent:
                    sent = convert_sent(sent, token_col, span_col, label_col)
                    if sent is not None:
                        w.write(json.dumps(sent) + '\n')
                    sent = []
        if sent:
            sent = convert_sent(sent, token_col, span_col, label_col)
            if sent is not None:
                w.write(json.dumps(sent) + '\n')


def json_to_mention_results(input_dir, output_dir, file_name,
                            bio_separator=' ', rev_entity_type=True):
    mention_type_list = ['nam', 'nom', 'pro', 'nam+nom+pro']
    file_type_list = ['bio', 'tab']
    writers = {}
    for mention_type in mention_type_list:
        for file_type in file_type_list:
            output_file = os.path.join(output_dir, '{}.{}.{}'.format(file_name,
                                                                     mention_type,
                                                                     file_type))
            writers['{}_{}'.format(mention_type, file_type)
                    ] = open(output_file, 'w')

    json_files = glob.glob(os.path.join(input_dir, '*.json'))
    doc_mention_count = defaultdict(int)
    for f in json_files:
        with open(f, 'r', encoding='utf-8') as r:
            for line in r:
                result = json.loads(line)
                doc_id = result['doc_id']
                tokens = result['tokens']
                token_ids = result['token_ids']
                bio_tokens = [[t, tid, 'O']
                              for t, tid in zip(tokens, token_ids)]
                # separate bio output
                for mention_type in ['NAM', 'NOM', 'PRO']:
                    tokens_tmp = deepcopy(bio_tokens)
                    for start, end, enttype, mentype, _ in result['graph']['entities']:
                        if mention_type == mentype:
                            tokens_tmp[start][-1] = 'B-{}'.format(enttype)
                            for token_idx in range(start + 1, end):
                                tokens_tmp[token_idx][-1] = 'I-{}'.format(
                                    enttype)
                    writer = writers['{}_bio'.format(mention_type.lower())]
                    for token in tokens_tmp:
                        writer.write(bio_separator.join(token) + '\n')
                    writer.write('\n')
                # combined bio output
                tokens_tmp = deepcopy(bio_tokens)
                for start, end, enttype, _, _ in result['graph']['entities']:
                    tokens_tmp[start][-1] = 'B-{}'.format(enttype)
                    for token_idx in range(start + 1, end):
                        tokens_tmp[token_idx][-1] = 'I-{}'.format(enttype)
                writer = writers['nam+nom+pro_bio']
                for token in tokens_tmp:
                    writer.write(bio_separator.join(token) + '\n')
                writer.write('\n')
                # separate tab output
                for mention_type in ['NAM', 'NOM', 'PRO']:
                    writer = writers['{}_tab'.format(mention_type.lower())]
                    # mention_count = 0
                    for start, end, enttype, mentype, _ in result['graph']['entities']:
                        if mention_type == mentype:
                            # mention_id = '{}-{}'.format(doc_id, mention_count)
                            mention_id = '{}-{}'.format(doc_id, doc_mention_count[doc_id])
                            doc_mention_count[doc_id] += 1
                            tab_line = mention_to_tab(
                                start, end, enttype, mentype, mention_id, tokens, token_ids,
                                rev_entity_type=rev_entity_type)
                            if len(tab_line) > 0:
                                writer.write(tab_line + '\n')
                # combined tab output
                writer = writers['nam+nom+pro_tab']
                # mention_count = 0
                for start, end, enttype, mentype, _ in result['graph']['entities']:
                    # mention_id = '{}-{}'.format(doc_id, mention_count)
                    mention_id = '{}-{}'.format(doc_id, doc_mention_count[doc_id])
                    doc_mention_count[doc_id] += 1
                    tab_line = mention_to_tab(
                        start, end, enttype, mentype, mention_id, tokens, token_ids,
                        rev_entity_type=rev_entity_type)
                    writer.write(tab_line + '\n')
    for w in writers:
        writers[w].close()
