from collections import defaultdict
import os
import sys
from typing import Counter
sys.path.append("./AIDA-Interchange-Format-master.m54/python")
sys.path.append("./AIDA-Interchange-Format-master.m54/python/aida_interchange")
from aida_interchange import aifutils
# from aida_interchange.aida_rdf_ontologies import AIDA_ANNOTATION
from aida_interchange.rdf_ontologies import ldc_ontology_m36 as LDC, interchange_ontology as AIDA
from aida_interchange.ldc_time_component import LDCTimeComponent, LDCTimeType
from aida_interchange.bounding_box import Bounding_Box
from aida_interchange.ldc_time_component import LDCTimeComponent, LDCTimeType
from aida_interchange.rdf_ontologies import ldc_ontology, interchange_ontology
from aida_interchange import claim
from aida_interchange import claim_component

from rdflib import Graph, Namespace, URIRef, term, Literal, BNode, RDF, XSD
from rdflib.namespace import ClosedNamespace
import ujson as json
# import json
import xml.etree.ElementTree as ET
import argparse
# from meta import prefix_ldc 
from postprocessing_extract_source import extract_source
# import elmoformanylangs
import numpy as np
import base64
from postprocessing_rename_turtle import load_doc_root_mapping
from xpo_read import load_xpo, format_type, format_role, format_relation, template


topic_type_map = {
}

def load_freebase(freebase_tab, edl_cs):
    # freebase_tab
    offset_link = defaultdict(lambda : defaultdict(float))
    for line in open(freebase_tab):
        line = line.rstrip('\n')
        tabs = line.split('\t')
        offset = tabs[3]
        link = tabs[4]
        if not link.startswith('NIL'):
            confidence = float(tabs[7])
            offset_link[offset][link] = confidence

    # edl_cs
    # entity_offset_mapping = defaultdict(list)
    confidence_dict = defaultdict(lambda : defaultdict(list))
    for line in open(edl_cs):
        line = line.rstrip('\n')
        tabs = line.split('\t')
        if line.startswith(':Entity') and 'mention' in tabs[1]:
            entity_id = id_normalize(tabs[0], language)
            offset = tabs[3]
            # entity_offset_mapping[entity_id].append(offset)
            for freebase_link in offset_link[offset]:
                confidence = offset_link[offset][freebase_link]
                confidence_dict[entity_id][freebase_link].append(confidence)

    freebase_link_map = defaultdict(lambda : defaultdict(lambda : defaultdict(float)))
    for entity_id in confidence_dict:
        for freebase_link in confidence_dict[entity_id]:
            mean = np.mean(confidence_dict[entity_id][freebase_link])
            max = np.max(confidence_dict[entity_id][freebase_link])
            # for offset in entity_offset_mapping[entity_id]:
            #     freebase_link_map[offset][freebase_link]['average_score'] = mean
            #     freebase_link_map[offset][freebase_link]['max_score'] = max
            freebase_link_map[entity_id][freebase_link]['average_score'] = mean
            freebase_link_map[entity_id][freebase_link]['max_score'] = max
    
    return freebase_link_map


def choose_elmo_model(lang, eng_elmo, ukr_elmo, rus_elmo):
    if lang.startswith('en'):
        return eng_elmo
    elif lang.startswith('uk'):
        return ukr_elmo
    elif lang.startswith('ru'):
        return rus_elmo


# def generate_trigger_emb(doc_id, start_offset, end_offset, ltf_dir, lang, eng_elmo, ukr_elmo, rus_elmo):
#     ltf_file_path = None
#     ltf_file_path = os.path.join(ltf_dir, doc_id + '.ltf.xml')
#     if os.path.exists(ltf_file_path):

#         tree = ET.parse(ltf_file_path)
#         root = tree.getroot()
#         for doc in root:
#             for text in doc:
#                 for seg in text:
#                     sent_tokens = []
#                     token_idxs = []
#                     seg_beg = int(seg.attrib["start_char"])
#                     seg_end = int(seg.attrib["end_char"])
#                     if start_offset >= seg_beg and end_offset <= seg_end:
#                         for token in seg:
#                             if token.tag == "TOKEN":
#                                 token_text = token.text
#                                 token_id = int(token.attrib["id"].split('-')[-1])
#                                 token_beg = int(token.attrib["start_char"])
#                                 token_end = int(token.attrib["end_char"])
#                                 if start_offset <= token_beg and end_offset >= token_end:
#                                     token_text = '<span style="color:blue">' + token_text + '</span>'
#                                     token_idxs.append(token_id)
#                                 sent_tokens.append(token_text)
#                     if len(token_idxs) > 0 and len(token_idxs) <= 5:
#                         elmo_model = choose_elmo_model(lang, eng_elmo, ukr_elmo, rus_elmo)
#                         sentence_emb = elmo_model.sents2elmo([sent_tokens])[0]
#                         trigger_embs = sentence_emb[token_idxs[0]:(token_idxs[-1]+1)]
#                         trigger_emb = np.mean(trigger_embs, axis=0)
#                         return trigger_emb
#     if ltf_file_path is None:
#         print('[ERROR]NoLTF %s' % doc_id)
#     return None


def load_entity_vec(ent_vec_files, ent_vec_dir):
    offset_vec = defaultdict(lambda: defaultdict(lambda: defaultdict(list))) # docid -> vectype -> end(headword) -> offset

    for ent_vec_file in ent_vec_files:
        ent_vec_type = ent_vec_file.split('/')[-1].replace('.mention.hidden.txt', '').replace('.trigger.hidden.txt', '')
        for line in open(os.path.join(ent_vec_dir, ent_vec_file)):
            line = line.rstrip('\n')
            tabs = line.split('\t')
            if len(tabs) == 3:
                offset = tabs[1]
                doc_id, start, end = parse_offset_str(offset)
                vec = np.array(tabs[2].split(','), dtype='f')
                # offset_vec[offset][ent_vec_type].append(vec)
                offset_vec[doc_id][ent_vec_type][end].append((start, end, vec))
    return offset_vec


def add_filetype(g, one_unique_ke, filetype_str):
    system = aifutils.make_system_with_uri(g, "http://www.uiuc.edu/fileType")
    file_type_json_object = {'fileType': filetype_str}
    file_type_json_content = json.dumps(file_type_json_object)
    aifutils.mark_private_data(g, one_unique_ke, file_type_json_content, system)


def transoffset_mapping(doc_id, start, end, translation_mapping):
    new_start = -1
    new_end = -1
    if translation_mapping is not None:
        # find the sentence offset
        
        for trans_start in translation_mapping[doc_id]:
            for trans_end in translation_mapping[doc_id][trans_start]:
                if start+2 >= int(trans_start) and end-2 <= int(trans_end):
                    new_start = translation_mapping[doc_id][trans_start][trans_end][0]
                    new_end = translation_mapping[doc_id][trans_start][trans_end][1]
                    break
            if new_start != -1:
                break
        if new_start == -1:
            print('No translation mapping', doc_id, start, end)
            for trans_start in translation_mapping[doc_id]:
                for trans_end in translation_mapping[doc_id][trans_start]:
                    if end <= int(trans_end):
                        # first start
                        new_start = translation_mapping[doc_id][trans_start][trans_end][0]
                        new_end = translation_mapping[doc_id][trans_start][trans_end][1]
                        break
                if new_start != -1:
                    break
    else:
        new_start = start
        new_end = end
    return new_start, new_end

def add_text_justification(g, doc_id, start, end, 
                        justification_confidence, justification_uri, system,
                        mention_str, mention_type, file_type, add_preflabel=False, 
                        SKOS=ClosedNamespace(uri=URIRef('http://www.w3.org/2004/02/skos/core#'), terms=['prefLabel']), doc_id_to_root_dict=None,
                        translation_mapping=None):
    new_start, new_end = transoffset_mapping(doc_id, start, end, translation_mapping)
    justification = aifutils.make_text_justification(g,  doc_id, new_start,
                                                            new_end, system, justification_confidence,
                                                            justification_uri)
    justification = aifutils.add_source_document_to_justification(g, justification, doc_id_to_root_dict[doc_id])
    # add prefLabel     
    if add_preflabel:
        g.add((justification, SKOS.prefLabel, Literal(mention_str))) 
    # add justificationType
    aifutils.mark_private_data(g, justification, json.dumps({'justificationType': mention_type}), system)
    # add fileType
    add_filetype(g, justification, file_type)
    return justification


def add_informative_justification(g, doc_id, start, end, 
                        justification_confidence, justification_uri, system, file_type, 
                        doc_id_to_root_dict=None,translation_mapping=None):
    new_start, new_end = transoffset_mapping(doc_id, start, end, translation_mapping)
    justification = aifutils.make_text_justification(g,  doc_id, new_start,
                                                            new_end, system, justification_confidence,
                                                            justification_uri)
    aifutils.add_source_document_to_justification(g, justification, doc_id_to_root_dict[doc_id])
    add_filetype(g, justification, file_type)
    return justification                                                    


def write_justification(g, ke_id, ke_type, nodes_needs_justifications, info_dict, file_type, system, offset_aif, doc_id, add_preflabel=False, doc_id_to_root_dict=None,translation_mapping=None):
    for offset in info_dict['mention']:
        # if offset != canonical_offset:
        doc_id_offset, start, end = parse_offset_str(offset)
        # print(doc_id_offset, doc_id, doc_id_offset == doc_id)
        if doc_id is not None and doc_id_offset == doc_id:
            justification_uri = "http://www.isi.edu/gaia/assertions/uiuc/%sjustification/%s/%s/%d/%d" % (ke_type, ke_id, doc_id, start, end)
            mention_confidence, mention_type, mention_str = info_dict['mention'][offset]
            justification = add_text_justification(g, doc_id, start, end, 
                        mention_confidence, justification_uri, system,
                        mention_str, mention_type, file_type, add_preflabel=add_preflabel,
                        doc_id_to_root_dict=doc_id_to_root_dict,translation_mapping=translation_mapping)
            # add mention to aida:justifiedBy
            aifutils.mark_justification(g, nodes_needs_justifications, justification)
            # save event offsets for event_coreference scores:
            if offset_aif is not None and ke_type == 'event':
                offset_aif[offset] = justification
            # add sentence
            json_object = {
                'mention_string': mention_str, 
                'sentence': get_context(doc_id, start, end, ltf_dir)
            }
            json_content = json.dumps(json_object)
            aifutils.mark_private_data(g, justification, json_content, aifutils.make_system_with_uri(g, "http://www.uiuc.edu/mention"))
    
    return offset_aif


def write_informative_justification(g, ke_id, ke_type, ke, info_dict, file_type, system, doc_id, doc_id_to_root_dict=None, translation_mapping=None):
    # add informative justification
    canonical_str, canonical_offset = info_dict['canonical_mention'][doc_id]
    doc_id_offset, start, end = parse_offset_str(canonical_offset)
    if doc_id is not None and doc_id_offset == doc_id:
        informative_uri = "http://www.isi.edu/gaia/assertions/uiuc/%s_informative_justification/%s/%s/%d/%d" % (ke_type, ke_id, doc_id, start, end)
        confidence = info_dict['confidence']
        informative_justification = add_informative_justification(g, doc_id, start, end, 
                        confidence, informative_uri, system, file_type, doc_id_to_root_dict,translation_mapping)
        # add canonical_mention to aida:informativeJustification
        aifutils.mark_informative_justification(g, ke, informative_justification)
        # add confidence to the ke
        aifutils.mark_confidence(g, ke, confidence, system)
        # add sentence
        json_object = {
            'mention_string': canonical_str, 
            'sentence': get_context(doc_id, start, end, ltf_dir)
        }
        json_content = json.dumps(json_object)
        aifutils.mark_private_data(g, informative_justification, json_content, aifutils.make_system_with_uri(g, "http://www.uiuc.edu/mention"))


def parse_offset_str(offset_str):
    doc_id = offset_str[:offset_str.rfind(':')]
    start = int(offset_str[offset_str.rfind(':') + 1:offset_str.rfind('-')])
    end = int(offset_str[offset_str.rfind('-') + 1:])
    return doc_id, start, end

def get_str_from_ltf(doc_id, start, end, ltf_dir):
    tokens = []

    ltf_file_path = os.path.join(ltf_dir, doc_id + '.ltf.xml')
    if not os.path.exists(ltf_file_path):
        return '[ERROR]NoLTF %s' % doc_id
    tree = ET.parse(ltf_file_path)
    root = tree.getroot()
    # valid = False
    for doc in root:
        for text in doc:
            for seg in text:
                for token in seg:
                    if token.tag == "TOKEN":
                        token_beg = int(token.attrib["start_char"])
                        token_end = int(token.attrib["end_char"])
                        if start <= token_beg and end >= token_end:
                            tokens.append(token.text)
                        # if start == token_beg:
                        #     valid = True
                        # if valid:
                        #     tokens.append(token.text)
                        # if end == token_end:
                        #     valid = False
    if len(tokens) > 0:
        return ' '.join(tokens)
    else:
        print('[ERROR]can not find the string with offset ', doc_id, start, end)
        # return None
        return get_str_from_rsd(doc_id, start, end, ltf_dir.replace('ltf', 'rsd'))

def get_str_from_rsd(doc_id, start, end, rsd_dir):
    rsd_file_path = os.path.join(rsd_dir, doc_id + '.rsd.txt')
    if os.path.exists(rsd_file_path):
        rsd_content = open(rsd_file_path).read()
        return rsd_content[start:end+1].replace('\n',' ')

def get_context(docid, start, end, ltf_dir):

    # tokens = []
    sentence = None

    ltf_file_path = os.path.join(ltf_dir, docid + '.ltf.xml')
    if not os.path.exists(ltf_file_path):
        return '[ERROR]NoLTF %s' % docid
    tree = ET.parse(ltf_file_path)
    root = tree.getroot()
    for doc in root:
        for text in doc:
            for seg in text:
                seg_beg = int(seg.attrib["start_char"])
                seg_end = int(seg.attrib["end_char"])
                if start >= seg_beg and end <= seg_end:
                    for token in seg:
                        if token.tag == "ORIGINAL_TEXT":
                            sentence = token.text
                            return sentence
                # if len(tokens) > 0:
                #     return tokens
    return sentence

def get_context_sentences(docid, start, end, ltf_dir):
     # tokens = []
    sentence = None

    ltf_file_path = os.path.join(ltf_dir, docid + '.ltf.xml')
    # print(ltf_file_path)
    # print(start, end)
    if not os.path.exists(ltf_file_path):
        return '[ERROR]NoLTF %s' % ltf_file_path
    tree = ET.parse(ltf_file_path)
    root = tree.getroot()
    sentence_before = ""
    sentence_after = ""
    read_next = False
    for doc in root:
        for text in doc:
            for seg in text:
                seg_beg = int(seg.attrib["start_char"])
                seg_end = int(seg.attrib["end_char"])
                # print(seg_beg, start)
                for token in seg:
                    if token.tag == "ORIGINAL_TEXT":
                        if read_next:
                            for token in seg:
                                if token.tag == "ORIGINAL_TEXT":
                                    sentence_after = token.text
                                    # print([sentence_before, sentence, sentence_after])
                                    return sentence_before, sentence, sentence_after
                        if start >= seg_beg and end <= seg_end:
                            sentence = token.text
                            read_next = True
                        else:
                            sentence_before = token.text
                        # if len(tokens) > 0:
                        #     return tokens
    return sentence_before, sentence, sentence_after

def get_translation(translation_json, ltf_dir, mapping_dir):
    str_mapping = defaultdict(set)
    translation_data = json.load(open(translation_json))
    for offset_str in translation_data:
        doc_id, start, end = parse_offset_str(offset_str)
        raw_str = get_str_from_ltf(doc_id, start, end, ltf_dir)
        for enstr_translated in translation_data[offset_str]:
            str_mapping[enstr_translated].add(str(raw_str))
    json.dump(str_mapping, open(os.path.join(mapping_dir,'str_trans_mapping.json'), 'w'), indent=4)
    return str_mapping

def get_translation_entity(entity_info_cs, mapping_dir):
    # for docid in docsent_mapping_trans2raw:
    #     for sent_beg_trans in docsent_mapping_trans2raw[docid]:
    #         for sent_end_trans in docsent_mapping_trans2raw[docid][sent_beg_trans]:
    #             for 
    mentions = Counter()
    for line in open(entity_info_cs):
        line = line.rstrip('\n')
        tabs = line.split('\t')

        if line.startswith(':Entity'):
            # entity_id = id_normalize(tabs[0], language)
            # if tabs[1] == 'type':
            #     entity_type = tabs[2].split(' ')[0].split('#')[-1].strip()
            #     entity_type = entity_type.replace('WEA.Projectile', 'WEA.ThrownProjectile')
            #     entity_info[entity_id]['type'] = entity_type
            #     # # DWD
            #     # if entity_type in ontology_data['entity']:
            #     #     entity_type_qnode = ontology_data['entity'][entity_type]
            #     #     entity_info[entity_id]['type_qnode'] = entity_type_qnode
            #     # else:
            #     #     print('wrong', entity_type, ontology_data['entity'].keys())
                
            if 'mention' == tabs[1]:
                mention = tabs[2][1:-1]
                mentions[mention] += 1
    writer = open(os.path.join(mapping_dir, 'entity_lst.txt'), 'w')
    for mention, num in mentions.most_common():
        if num > 1:
            writer.write(mention)
            writer.write('\n')
    writer.flush()
    writer.close()

def get_translation_mapping(name_mapping_file):
    str_mapping = defaultdict(set)
    for line in open(name_mapping_file):
        line = line.rstrip('\n')
        tabs = line.split('\t')
        raw_str = tabs[0]
        en_str = tabs[1]
        if raw_str.lower() != en_str.lower():
            str_mapping[en_str].add(raw_str)
    return str_mapping

def load_canonical_mention(tabs, info_dict, language, validate_offset):
    offset = tabs[3]
    mention_str = tabs[2][1:-1]
    doc_id, start, end = parse_offset_str(offset)
    if validate_offset:
        mention_str_ltf = get_str_from_ltf(doc_id, start, end, ltf_dir)
        assert mention_str == mention_str_ltf
    info_dict['confidence'] = float(tabs[4])
    if 'canonical_mention' not in info_dict:
        info_dict['canonical_mention'] = dict()
    info_dict['canonical_mention'][doc_id] = (mention_str, offset)
    info_dict['filetype'] = '%s' % (language)
    return doc_id

def load_mention(tabs, info_dict, validate_offset):
    offset = tabs[3]
    mention_type = tabs[1].replace(".actual", "")
    mention_confidence = float(tabs[4])
    mention_str = tabs[2][1:-1]
    if validate_offset:
        doc_id, start, end = parse_offset_str(offset)
        mention_str_ltf = get_str_from_ltf(doc_id, start, end, ltf_dir)
        assert mention_str == mention_str_ltf
    if 'mention' not in info_dict:
        info_dict['mention'] = dict()
    info_dict['mention'][offset] = (mention_confidence, mention_type, mention_str)
    return offset

def id_normalize(id_raw, language):
    return language.upper()+'_'+id_raw[1:]

def convert_data_gdate(date):
    # date --> "yyyy-mm-dd"
    # return (gYear, gMonth, gDay)
    date = date.strip().split("-")
    # Since splits done on "-", "_" used to represent negative.
    # According to w3c, earliest possible year for gYear is -9999 = 10,000 BC.
    date = [x.replace("\"", "").replace("_", "-") for x in date]
    added_strings = ["", "--", "---"]
    date = [add_str+x for add_str, x in zip(added_strings, date)]
    gdate_types = [XSD.gYear, XSD.gMonth, XSD.gDay]
    gdate = (Literal(x, datatype=dt) for x, dt in zip(date, gdate_types))
    return tuple(gdate)

def convert_data_date(date):
    if 'inf' in date:
        return tuple([None, None, None])
    # date --> "yyyy-mm-dd"
    # return (gYear, gMonth, gDay)
    date = date[1:-1].strip().split("-")
    # Since splits done on "-", "_" used to represent negative.
    # According to w3c, earliest possible year for gYear is -9999 = 10,000 BC.
    # date = [x.replace("\"", "").replace("_", "-") for x in date]
    added_strings = ["", "--", "---"]
    date = [add_str+x for add_str, x in zip(added_strings, date)]
    # gdate_types = [XSD.gYear, XSD.gMonth, XSD.gDay]
    # gdate = (Literal(x, datatype=dt) for x, dt in zip(date, gdate_types))
    return tuple(date) #tuple(gdate)


def date_leq(date1, date2):
    # Returns True if date1 <= date2, else False
    for v1, v2 in zip(date1, date2):
        if v1 > v2:
            return False
    return True


def validate_date_entry(v):
    t1, t2, t3, t4 = v
    pairs = [[t1, t2], [t2, t3], [t3, t4]]
    for pair in pairs:
        if not date_leq(*pair):
            return False
    return True

def load_event_coreference_score(coreference_score_tab):
    coreference_score = defaultdict(lambda : defaultdict(lambda : defaultdict(str)))
    for line in open(coreference_score_tab):
        # IC001VBFN       694,700 2887,2893       0.399422
        line = line.rstrip('\n')
        tabs = line.split('\t')
        if len(tabs) == 4:
            doc_id = tabs[0]
            confidence = float(tabs[3])
            offset1_start, offset1_end = tabs[1].split(',')
            offset1_end = str(int(offset1_end) - 1)
            offset1 = '%s:%s-%s' % (doc_id, offset1_start, offset1_end)
            offset2_start, offset2_end = tabs[2].split(',')
            offset2_end = str(int(offset2_end) - 1)
            offset2 = '%s:%s-%s' % (doc_id, offset2_start, offset2_end)
            # offset1 = '%s:%s' % (doc_id, tabs[1].replace(',', '-'))
            # offset2 = '%s:%s' % (doc_id, tabs[2].replace(',', '-'))
            coreference_score[doc_id][offset1][offset2] = confidence
            coreference_score[doc_id][offset2][offset1] = confidence
        else:
            print('coreference score can not load in ', line)
    return coreference_score



def load_source_tab(source_tab):
    source_dict = defaultdict(str)
    for line in open(source_tab):
        line = line.rstrip('\n')
        tabs = line.split('\t')
        child_id = tabs[3]
        # source = tabs[-1]
        url = tabs[4]
        source = extract_source(url)
        source_dict[child_id] = source
    return source_dict


def load_cs(input_cs, ontology_data, qnode_name_dict, language, validate_offset=False, single_type=False):
    doc_ke = defaultdict(lambda: defaultdict(set))
    entity_info = defaultdict(lambda : defaultdict())
    evt_info = defaultdict(lambda : defaultdict())
    evt_args = defaultdict(lambda : defaultdict(lambda: defaultdict(list)))
    evt_args_qnode = defaultdict(lambda : defaultdict())
    qnode_dict = defaultdict(lambda : defaultdict(lambda: Counter()))
    evt_ignore = set()
    rel_idx = 0
    if single_type:
        entity_type_confidence_dict = dict()
    for line in open(input_cs):
        line = line.rstrip('\n')
        tabs = line.split('\t')

        if line.startswith(':Entity'):
            entity_id = id_normalize(tabs[0], language)
            if tabs[1] == 'type':
                entity_type = tabs[2].split(' ')[0].split('#')[-1].strip()
                entity_type = entity_type.replace('WEA.Projectile', 'WEA.ThrownProjectile')
                entity_info[entity_id]['type'] = entity_type
                # # DWD
                # if entity_type in ontology_data['entity']:
                #     entity_type_qnode = ontology_data['entity'][entity_type]
                #     entity_info[entity_id]['type_qnode'] = entity_type_qnode
                # else:
                #     print('wrong', entity_type, ontology_data['entity'].keys())
                
            elif 'canonical_mention' in tabs[1]:
                mention_doc_id = load_canonical_mention(tabs, entity_info[entity_id], language, validate_offset)
                # doc_ke[doc_id]['entity'].add(entity_id)

                # if mention_doc_id == doc_id:
                #     if tabs[1] == 'mention':
                #         if 'name' not in entity_info[entity_id]:
                #             entity_info[entity_id]['name'] = list()
                #         entity_info[entity_id]['name'].append(tabs[2][1:-1])
                #     elif tabs[1] == 'nominal_mention' or tabs[1] == 'pronominal_mention':
                #         if entity_type.split('.')[0] in ['MHI', 'MON', ' RES', 'TTL', 'VAL']:
                #             if 'name' not in entity_info[entity_id]:
                #                 entity_info[entity_id]['name'] = list()
                #             entity_info[entity_id]['name'].append(tabs[2][1:-1])
            elif 'mention' in tabs[1]:
                mention_offset = load_mention(tabs, entity_info[entity_id], validate_offset)
                mention_doc_id, start, end = parse_offset_str(mention_offset)
                doc_ke[mention_doc_id]['entity'].add(entity_id)
                # check entity Qnodes
                mention_str = tabs[2][1:-1].lower()
                if mention_str in qnode_name_dict['entity']:
                    qnode_mapped = qnode_name_dict['entity'][mention_str]
                    if 'type_qnode' not in entity_info[entity_id]:
                        entity_info[entity_id]['type_qnode'] = dict()
                    entity_info[entity_id]['type_qnode'][qnode_mapped] = 1.0
                    # print('mapped entity Qnodes', mention_str)
                    qnode_dict[tabs[2][1:-1]]['type_qnode'][qnode_mapped] += 1
                # if mention_doc_id == doc_id:
                if tabs[1] == 'mention':
                    entity_info[entity_id]['hasName'] = True
                    # if 'name' not in entity_info[entity_id]:
                    #     entity_info[entity_id]['name'] = list()
                    # entity_info[entity_id]['name'].append(tabs[2][1:-1])
                elif tabs[1] == 'nominal_mention' or tabs[1] == 'pronominal_mention':
                    if entity_type.split('.')[0] in ['MHI', 'MON', ' RES', 'TTL', 'VAL']:
                        # if 'name' not in entity_info[entity_id]:
                        #     entity_info[entity_id]['name'] = list()
                        # entity_info[entity_id]['name'].append(tabs[2][1:-1])
                        entity_info[entity_id]['hasName'] = True
            elif 'link' == tabs[1]:
                link_target = tabs[2].replace('NIL', 'NILQ')
                # if link_target.startswith('NIL'):
                #     continue
                link_target = '%s' % (link_target.split(':')[-1])
                if len(tabs) > 3:
                    link_confidence = float(tabs[3])
                else:
                    link_confidence = 1.0
                link_confidence_maxpool = None
                if len(tabs) == 5:
                    link_confidence_maxpool = float(tabs[4])
                if 'link' not in entity_info[entity_id]:
                    entity_info[entity_id]['link'] = dict()
                entity_info[entity_id]['link'][link_target] = (link_confidence, link_confidence_maxpool)
                # # DWD
                # if not link_target.startswith('NIL'):
                #     entity_info[entity_id]['type_qnode'] = dict()
                #     entity_info[entity_id]['type_qnode'][link_target] = link_confidence
                for offset in entity_info[entity_id]['mention']:
                    mention_confidence, mention_type, mention_str = entity_info[entity_id]['mention'][offset]
                    qnode_dict[mention_str]['qnode'][tabs[2]] += 1
            elif 'typelink' == tabs[1]:
                if 'type_qnode' not in entity_info[entity_id]:
                    entity_info[entity_id]['type_qnode'] = dict()
                entity_info[entity_id]['type_qnode'][tabs[2]] = 0.95
                for offset in entity_info[entity_id]['mention']:
                    mention_confidence, mention_type, mention_str = entity_info[entity_id]['mention'][offset]
                    qnode_dict[mention_str]['type_qnode'][tabs[2]] += 1
            # elif 'http' in tabs[1]:
            elif len(tabs) > 3 and (tabs[2].startswith(':Entity') or tabs[2].startswith(':Filler_') or tabs[2].startswith(':Event_')):
                # relation
                rel_type = tabs[1].split('#')[-1].strip()
                if 'Affiliation' in rel_type:
                    entity_info[entity_id]['affiliation'] = (id_normalize(tabs[2], language), tabs[3])
                if format_relation(rel_type) not in ontology_data['relation']:
                    print('NOTYPE REL', rel_type, format_relation(rel_type))
                    continue
                rel_offset = tabs[3]
                rel_confidence = float(tabs[4])
                doc_rel, rel_start, rel_end = parse_offset_str(rel_offset)
                rel_id = id_normalize(':Relation_{:0>6}'.format(rel_idx), language)
                rel_idx += 1
                doc_ke[doc_rel]['relation'].add(rel_id)
                evt_info[rel_id]['type'] = rel_type
                evt_info[rel_id]['type_qnode'] = dict()
                rel_type_qnode = ontology_data['relation'][format_relation(rel_type)]['qnode']
                evt_info[rel_id]['type_qnode'][rel_type_qnode] = 1.0
                
                rel_mention_str = ''
                rel_mention_type = ''
                evt_info[rel_id]['confidence'] = float(tabs[4])
                evt_info[rel_id]['canonical_mention'] = dict()
                evt_info[rel_id]['canonical_mention'][doc_rel] = (rel_mention_str, rel_offset)
                evt_info[rel_id]['filetype'] = '%s' % (language)
                evt_info[rel_id]['mention'] = dict()
                evt_info[rel_id]['mention'][rel_offset] = (rel_confidence, rel_mention_type, rel_mention_str)   

                arg_id = id_normalize(tabs[2], language)
                evt_args[rel_id]['A0'][entity_id].append( (rel_offset, rel_offset, rel_confidence) )
                evt_args_qnode[rel_id]['A0_qnode'] = ontology_data['relation_arg'][rel_type_qnode]['A0']
                evt_args[rel_id]['A1'][arg_id].append( (rel_offset, rel_offset, rel_confidence) ) #(mention_offset, arg_offset, arg_confidence) )
                evt_args_qnode[rel_id]['A1_qnode'] = ontology_data['relation_arg'][rel_type_qnode]['A1']

                
        if line.startswith(':Event') or line.startswith(':Relation'):
            ke_type = line[1:line.find('_')].lower()
            evt_id = id_normalize(tabs[0], language)
            if evt_id in evt_ignore:
                continue
            if tabs[1] == 'type':
                evt_type = format_type(tabs[2].split('#')[-1].strip())
                if evt_type is None:
                    evt_ignore.add(evt_id)
                    continue
                evt_info[evt_id]['type'] = tabs[2].split('#')[-1].strip() #evt_type
                # DWD
                if 'type_qnode' not in evt_info[evt_id]:
                    evt_info[evt_id]['type_qnode'] = dict()
                if evt_type in ontology_data['event']:
                    evt_type_qnode = ontology_data['event'][evt_type]['qnode']
                    evt_info[evt_id]['type_qnode'][evt_type_qnode] = 1.0
                elif evt_type.split('.')[-1] in ontology_data['event_subtype']:
                    evt_type_qnode = ontology_data['event_subtype'][evt_type.split('.')[-1]]['qnode']
                    evt_info[evt_id]['type_qnode'][evt_type_qnode] = 1.0
                elif evt_type in qnode_name_dict['event']:
                    evt_type_qnode = qnode_name_dict['event'][evt_type]
                    evt_info[evt_id]['type_qnode'][evt_type_qnode] = 0.9
                else:
                    print('NOTYPE Event ', evt_type, evt_info[evt_id]['type'])
            elif 'canonical_mention' in tabs[1]:
                doc_id = load_canonical_mention(tabs, evt_info[evt_id], language, validate_offset)
                # doc_ke[doc_id][ke_type].add(evt_id)
            elif 'mention' in tabs[1]:
                mention_offset = load_mention(tabs, evt_info[evt_id], validate_offset)    
                mention_doc_id, start, end = parse_offset_str(mention_offset)
                doc_ke[mention_doc_id][ke_type].add(evt_id)
                # check event Qnodes
                mention_str = tabs[2][1:-1].lower()
                if mention_str in qnode_name_dict['event']:
                    evt_type_qnode_mapped = qnode_name_dict['event'][mention_str]
                    if 'type_qnode' not in evt_info[evt_id]:
                        evt_info[evt_id]['type_qnode'] = dict()
                    evt_info[evt_id]['type_qnode'][evt_type_qnode_mapped] = 0.8
                    # print('mapped event Qnodes', mention_str)
            elif len(tabs) > 3 and (tabs[2].startswith(':Entity') or tabs[2].startswith(':Filler_') or tabs[2].startswith(':Event_')):
                role = tabs[1].split('#')[-1].replace(".actual", "").strip() # no other label than ".actual" for now
                role_short = role.split('_')[-1]
                role = role_short
                arg_id = id_normalize(tabs[2], language)
                # if arg_id not in doc_ke[doc_id]['entity'] and arg_id not in doc_ke[doc_id]['event']:
                #     continue
                arg_offset = tabs[3]
                arg_confidence = float(tabs[4])
                evt_args[evt_id][role][arg_id].append( (mention_offset, arg_offset, arg_confidence) )
                for type_qnode in evt_info[evt_id]['type_qnode']:
                    if role_short in ontology_data['event_arg'][type_qnode]:
                        evt_args_qnode[evt_id][role+'_qnode'] = ontology_data['event_arg'][type_qnode][role_short]
                    roles_format = format_role(' '+role_short+' ').split('_')
                    for role_format in roles_format:
                        role_format = role_format.strip()
                        if role_format in ontology_data['event_arg'][type_qnode]:
                            evt_args_qnode[evt_id][role+'_qnode'] = ontology_data['event_arg'][type_qnode][role_format]
                            break
                    if role+'_qnode' not in evt_args_qnode[evt_id]: 
                        print('NOTYPE Role', role_short, format_role(' '+role_short+' '), entity_info[arg_id]['canonical_mention'][doc_id][0], evt_id, arg_id, mention_offset, mention_str, type_qnode, ontology_data['event_arg'][type_qnode].keys())
            elif len(tabs) > 2 and tabs[1].startswith('t') and len(tabs[1]) == 2:
                t_num = tabs[1]
                date = tabs[2]
                # for event_id, t_num, date in four_tuples:
                num = int(t_num[1:]) - 1
                # if "inf" not in date:
                #     date = convert_data_gdate(date)
                # else:
                #     if num < 3:
                #         date = convert_data_gdate("_9999-01-01")
                #     else:
                #         date = convert_data_gdate("9999-12-31")
                date = convert_data_date(date)
                if 'time' not in evt_info[evt_id]: 
                    evt_info[evt_id]['time'] = [None, None, None, None]
                evt_info[evt_id]['time'][num] = date
            elif tabs[1] == 'polarity':
                evt_info[evt_id]['polarity'] = tabs[2]
            elif tabs[1] == 'modality':
                evt_info[evt_id]['modality'] = tabs[2]
            elif tabs[1] == 'genericity':
                evt_info[evt_id]['genericity'] = tabs[2]
            # POLARITY_TYPES = ['Negative', 'Positive']
            # MODALITY_TYPES = ['Asserted', 'Other']
            # GENERICITY_TYPES = ['Generic', 'Specific']
            # TENSE_TYPES = ['Unspecified', 'Past', 'Future', 'Present']
            # REALIS_TYPES = ['actual', 'generic', 'other']

    for entity_id in entity_info:
        if 'type' not in entity_info[entity_id]:
                print('Do not have entity type', entity_id, entity_info[entity_id])
                
    return doc_ke, entity_info, evt_info, evt_args, evt_args_qnode, qnode_dict

def load_claim_json(claim_json):
    claim_data = json.load(open(claim_json))
    return claim_data

def gen_ttl(claim_data, doc_ke, entity_info, evt_info, evt_args, evt_args_qnode, qnode_dict, 
            SKOS, output_ttl_dir, evt_coref_score=None, source_dict=None, 
            freebase_links=None, fine_grained_entity_dict=None, 
            offset_event_vec=None, offset_entity_vec=None, doc_id_to_root_dict=None,
            ltf_dir=None, event_embedding_from_file=False, eng_elmo=None, ukr_elmo=None, rus_elmo=None,
            translation_mapping=None, str_mapping=None, only_qnode=True):
    LDC_namespace = Namespace(LDC.NAMESPACE)
    AIDA_namespace = Namespace(AIDA.NAMESPACE)
    CLAIM_namespace = Namespace('https://www.caci.com/claim-example#')

    claim_data_new = dict()
    for doc_id in doc_ke:
        # TODO: fix the wrong doc id
        # if 'L0C04ATB6' != doc_id:
        #     continue
        # print('entity', doc_ke[doc_id]['entity'])
        if doc_id not in claim_data:
            print('doc_id not in the claim result', doc_id)
            continue
        if doc_id_to_root_dict is not None:
            root_doc_id = doc_id_to_root_dict[doc_id]
        else:
            root_doc_id = ""

        g = aifutils.make_graph()
        g.bind('skos', SKOS.uri)
        g.bind('ldcOnt', LDC.NAMESPACE) # g.bind('ldc', LDC_uri)
        g.bind('ex', CLAIM_namespace)
        system = aifutils.make_system_with_uri(g, "http://www.uiuc.edu")
        # add_entity:
        entities_aif = dict()
        for entity_id in doc_ke[doc_id]['entity']:
            entity_uri = "http://www.isi.edu/gaia/entities/uiuc/%s/%s" % (doc_id, entity_id)
            ent = aifutils.make_entity(g, entity_uri, system)
            entities_aif[entity_id] = ent
            
            entity_needs_justifications = set()
            entity_needs_justifications.add(ent)
            file_type=entity_info[entity_id]['filetype']
            add_filetype(g, ent, file_type)
            
            # # add type assertions
            # if 'type' not in entity_info[entity_id]:
            #     print('Do not have entity type', entity_id, entity_info[entity_id])
            #     try:
            #         entity_type_qnode = entity_info[entity_id]['type_qnode']
            #     except:
            #         print('Do not have entity type', entity_id, entity_info[entity_id])
            #         exit
            #     type_assertion_uri = "http://www.isi.edu/gaia/assertions/uiuc/entitytype/%s/%s/%s" % (doc_id, entity_id, entity_type_cs)
            #     entity_type = Literal(entity_type_qnode, datatype=XSD.string) #LDC_namespace[entity_type_cs]
            #     entity_type_confidence = 1.0
                
            #     type_asser = aifutils.mark_type(g, type_assertion_uri, ent, entity_type, system, entity_type_confidence)
            #     aifutils.mark_private_data(g, max_type_assertion, json.dumps({'type': 'canonical_type'}), system)
            #     entity_needs_justifications.add(type_asser)
            # else:
            #     max_type_confidence = 0
            #     max_type_assertion = None
            #     max_type = ''
            #     for entity_type_cs in entity_info[entity_id]['type']:
            #         type_assertion_uri = "http://www.isi.edu/gaia/assertions/uiuc/entitytype/%s/%s/%s" % (doc_id, entity_id, entity_type_cs)
            #         # entity_type =  #LDC_namespace[entity_type_cs]
            #         # entity_type_confidence = entity_info[entity_id]['type'][entity_type_cs]
                    
            #         type_asser = aifutils.mark_type(g, type_assertion_uri, ent, Literal(entity_info[entity_id]['type_qnode'], datatype=XSD.string), system, entity_type_confidence)
            #         aifutils.mark_private_data(g, type_assertion_uri, json.dumps({'type': entity_type_cs}), system)
            #         # if entity_type_confidence > max_type_confidence:
            #         #     max_type_confidence = entity_type_confidence
            #         #     max_type_assertion = type_asser
            #         #     max_type = entity_type_cs
            #         max_type = entity_type
            #         max_type_assertion = type_asser
            #         entity_needs_justifications.add(type_asser)
            #     # aifutils.mark_private_data(g, max_type_assertion, json.dumps({'typeConfidence': 'canonical_type'}), system)
            entity_type_cs = entity_info[entity_id]['type']
            # print(entity_type_cs)
            for type_qnode_ in entity_info[entity_id]['type_qnode']:
                type_assertion_uri = URIRef("http://www.isi.edu/gaia/assertions/uiuc/entitytype/%s/%s/%s/%s" % (doc_id, entity_id, entity_type_cs, type_qnode_))
                type_qnode_confidence = entity_info[entity_id]['type_qnode'][type_qnode_]
                type_asser = aifutils.mark_type(g, type_assertion_uri, ent, Literal(type_qnode_, datatype=XSD.string), system, type_qnode_confidence)
                aifutils.mark_private_data(g, type_assertion_uri, json.dumps({'ldctype': entity_type_cs}), system)
                entity_needs_justifications.add(type_asser)
            max_type = entity_type_cs
            
            # add informative justification
            write_informative_justification(g, entity_id, 'entity', ent, entity_info[entity_id], file_type, system, doc_id_to_root_dict=doc_id_to_root_dict, doc_id=doc_id, translation_mapping=translation_mapping)
            
            # add justifications
            write_justification(g, entity_id, 'entity', entity_needs_justifications, entity_info[entity_id], file_type, system, offset_aif=None, add_preflabel=False, doc_id_to_root_dict=doc_id_to_root_dict, doc_id=doc_id, translation_mapping=translation_mapping)

            # add cluster
            entity_cluster = aifutils.make_cluster_with_prototype(g, "http://www.isi.edu/gaia/clusters/uiuc/entity/%s/%s" % (doc_id, entity_id),
                                                                  ent, system)
            aifutils.mark_as_possible_cluster_member(g, ent, entity_cluster, 0.9, system)   

            # add linking info
            if 'link' in entity_info[entity_id]:
                # max_link = None
                # max_link_conf = 0
                for link_target in entity_info[entity_id]['link']:
                    link_confidence, link_confidence_maxpool = entity_info[entity_id]['link'][link_target]
                    # g.add( (ent, AIDA_namespace.componentIdentity, Literal(link_confidence_maxpool, datatype=XSD.string)) )
                    link_assertion = aifutils.link_to_external_kb(g, ent, link_target, system, link_confidence)

                    # # append multiple confidence (max pool vs min pool)
                    # if link_confidence_maxpool is not None:
                    #     system_maxpool = aifutils.make_system_with_uri(g, "http://www.uiuc.edu/EDL_LORELEI_maxPool")
                    #     aifutils.mark_confidence(g, link_assertion, link_confidence_maxpool, system_maxpool)

                    # if link_confidence > max_link_conf:
                    #     max_link = link_target
                    #     max_link_conf = link_confidence
                
                # # add cross-modal coreference based on entity linking
                # corefer_id = max_link.split(':')[-1]
                # system_corefer = aifutils.make_system_with_uri(g, "http://www.uiuc.edu/coreference")
                # corefer_id_encoded = base64.b64encode(('%s%s' % (root_doc_id, corefer_id)).encode('utf-8')).decode("utf-8")
                # corefer_json_dict = {'coreference': corefer_id_encoded} #str(uuid.UUID(corefer_id).hex)}
                # corefer_json_content = json.dumps(corefer_json_dict)
                # aifutils.mark_private_data(g, ent, corefer_json_content, system_corefer)

            # TODO
            # add hasName/textValue
            # if 'name' in entity_info[entity_id]:
            if 'hasName' in entity_info[entity_id] and entity_info[entity_id]['hasName'] == True:
                # try:
                if max_type.split('.')[0] in ['PER', 'ORG', 'GPE', 'FAC', 'LOC', 'WEA', 'VEH', 'LAW']:
                    # for name_str_ in entity_info[entity_id]['name']:
                    #     aifutils.mark_name(g, ent, name_str_)
                    name_str_, offset_ = entity_info[entity_id]['canonical_mention'][doc_id]
                    aifutils.mark_name(g, ent, name_str_)
                    # add hasName
                    if str_mapping is not None:
                        if name_str_ in str_mapping:
                            for str_raw in str_mapping[name_str_]:
                                aifutils.mark_name(g, ent, str_raw)
                if max_type.split('.')[0] in ['MHI', 'MON', ' RES', 'TTL', 'VAL']:
                    # for text_value_str_ in entity_info[entity_id]['name']:
                    #     aifutils.mark_text_value(g, ent, text_value_str_)
                    text_value_str_, offset_ = entity_info[entity_id]['canonical_mention'][doc_id]
                    aifutils.mark_text_value(g, ent, text_value_str_)
                    # add hasName
                    if str_mapping is not None:
                        if text_value_str_ in str_mapping:
                            for str_raw in str_mapping[text_value_str_]:
                                aifutils.mark_text_value(g, ent, str_raw)
                # except:
                #     if entity_type_cs.split('.')[0] in ['PER', 'ORG', 'GPE', 'FAC', 'LOC', 'WEA', 'VEH', 'LAW']:
                #         for name_str_ in entity_info[entity_id]['name']:
                #             aifutils.mark_name(g, ent, name_str_)
                #     if entity_type_cs.split('.')[0] in ['MHI', 'MON', ' RES', 'TTL', 'VAL']:
                #         for text_value_str_ in entity_info[entity_id]['name']:
                #             aifutils.mark_text_value(g, ent, text_value_str_)

            # add freebase link
            if freebase_links is not None:
                if entity_id in freebase_links:
                    freebase_link = freebase_links[entity_id]
                    system_freebase = aifutils.make_system_with_uri(g, "http://www.uiuc.edu/EDL_Freebase")
                    freebase_json_content = json.dumps({'freebase_link': freebase_link})
                    aifutils.mark_private_data(g, ent, freebase_json_content, system_freebase)

                    # append EDL fine_grained_data
                    if fine_grained_entity_dict is not None:
                        linking_info = sorted(freebase_link.items(), key=lambda x: x[1]['average_score'], reverse=True)[0][0]
                        if linking_info in fine_grained_entity_dict:
                            fine_grained_json_object = fine_grained_entity_dict[linking_info]
                            fine_grained_json_content = json.dumps({'finegrained_type': fine_grained_json_object})
                            system_fine = aifutils.make_system_with_uri(g, "http://www.uiuc.edu/EDL_FineGrained")
                            aifutils.mark_private_data(g, ent, fine_grained_json_content, system_fine)
            
            # # add entity vec
            # entity_vecs = list()
            # for offset in entity_info[entity_id]['mention']:
            #     doc_id, start_offset, end_offset = parse_offset_str(offset)
            #     for ent_vec_type in offset_entity_vec[doc_id]:
            #         if len(doc_ke[doc_id]['entity']) > 700:
            #             for (vec_start, vec_end, vec) in offset_entity_vec[doc_id][ent_vec_type][end_offset]:
            #                 if vec_start >= start_offset and vec_end <= end_offset:
            #                     entity_vecs.append(vec)
            #         else:
            #             for end_ in offset_entity_vec[doc_id][ent_vec_type]:
            #                 for (vec_start, vec_end, vec) in offset_entity_vec[doc_id][ent_vec_type][end_]:
            #                     if vec_start >= start_offset and vec_end <= end_offset:
            #                         entity_vecs.append(vec)
            # if len(entity_vecs) > 0:
            #     entity_vec = np.average(entity_vecs, 0)
            #     system_vec = aifutils.make_system_with_uri(g, "http://www.uiuc.edu/entity_representations")
            #     ent_vec_json_object = {'entity_vec_space': ent_vec_type,
            #                            'entity_vec': ','.join(['%0.8f' % dim for dim in entity_vec])}
            #     ent_vec_json_content = json.dumps(ent_vec_json_object)
            #     aifutils.mark_private_data(g, ent, ent_vec_json_content, system_vec)


        print('event', len(doc_ke[doc_id]['event']))
        print('relation', len(doc_ke[doc_id]['relation']))
        # add_evt and relation:
        offset_aif = dict()
        for ke_type in ['event', 'relation']:
            for evt_id in doc_ke[doc_id][ke_type]:
                evt_uri = "http://www.isi.edu/gaia/%ss/uiuc/%s/%s" % (ke_type, doc_id, evt_id)
                if ke_type == 'event':
                    evt = aifutils.make_event(g, evt_uri, system)
                elif ke_type == 'relation':
                    evt = aifutils.make_relation(g, evt_uri, system)
                file_type = evt_info[evt_id]['filetype']
                add_filetype(g, evt, file_type)
                entities_aif[evt_id] = evt

                # add cluster
                evt_cluster = aifutils.make_cluster_with_prototype(g, "http://www.isi.edu/gaia/clusters/uiuc/%ss/%s/%s" % (ke_type, doc_id, evt_id),
                                                                    evt, system)
                aifutils.mark_as_possible_cluster_member(g, evt, evt_cluster, evt_info[evt_id]['confidence'], system)
                
                # add type assertions
                evt_type_cs = evt_info[evt_id]['type']
                # TODO: map qnode
                # evt_type_qnode = AIDA_namespace.none
                if 'type_qnode' in evt_info[evt_id]:
                    for type_qnode_ in evt_info[evt_id]['type_qnode']:
                        evt_type_qnode = Literal(type_qnode_, datatype=XSD.string)
                        type_confidence = evt_info[evt_id]['type_qnode'][type_qnode_]
                        # confidence = evt_info[evt_id]['confidence']
                        type_assertion_uri = URIRef("http://www.isi.edu/gaia/assertions/uiuc/%stype/%s/%s/%s/%s" % (ke_type, doc_id, evt_id, evt_type_cs,type_qnode_))
                        type_asser = aifutils.mark_type(g, type_assertion_uri, evt, evt_type_qnode, system, type_confidence)
                        aifutils.mark_private_data(g, type_assertion_uri, json.dumps({'ldctype': evt_type_cs}), system)
                        # g.add( (evt, AIDA_namespace.componentIdentity, Literal(evt_info[evt_id]['type_qnode'], datatype=XSD.string)) )
                else:
                    print('no type qnode for event', evt_type_cs)
                # evt_type = LDC_namespace[evt_type_cs]
                
                

                # add informative justification
                write_informative_justification(g, evt_id, ke_type, evt, evt_info[evt_id], file_type, system, doc_id_to_root_dict=doc_id_to_root_dict,doc_id=doc_id,translation_mapping=translation_mapping)

                # add justifications
                offset_aif = write_justification(g, evt_id, ke_type, [evt], evt_info[evt_id], file_type, system,  doc_id=doc_id, offset_aif=offset_aif, add_preflabel=False, doc_id_to_root_dict=doc_id_to_root_dict, translation_mapping=translation_mapping)

                # add roles
                for role in evt_args[evt_id]:
                    if role+'_qnode' not in evt_args_qnode[evt_id]:
                        continue
                    subject_role = evt_args_qnode[evt_id][role+'_qnode'] #role #LDC_namespace[role]
                    for arg_id in evt_args[evt_id][role]:
                        # for arg_offset, arg_confidence in evt_args[evt_id][role][arg_id]:  ?????????
                        trigger_arg_offset, arg_offset, arg_confidence = evt_args[evt_id][role][arg_id][0]
                        role_uri = "http://www.isi.edu/gaia/assertions/uiuc/%sarg/%s/%s/%s/%s/%s" % (ke_type, doc_id, evt_id, evt_type_cs, role, arg_id)
                        role_doc_id, role_start, role_end = parse_offset_str(arg_offset)
                        role_justi_uri = "http://www.isi.edu/gaia/assertions/uiuc/%sarg_justification/%s/%s/%s/%s/%s/%s/%d/%d" % (ke_type, doc_id, evt_id, evt_type_cs, role, arg_id, role_doc_id, role_start, role_end)
                        subject_resource = entities_aif[arg_id]
                        role_asser = aifutils.mark_as_argument(g, evt, subject_role, subject_resource, system, arg_confidence, uri=role_uri)
                        trigger_doc_id, trigger_start, trigger_end = parse_offset_str(trigger_arg_offset)
                        role_justification_trigger = aifutils.make_text_justification(g, trigger_doc_id, trigger_start,
                                                                                trigger_end, system, arg_confidence)
                        aifutils.add_source_document_to_justification(g, role_justification_trigger, doc_id_to_root_dict[trigger_doc_id])
                        role_justification_arg = aifutils.make_text_justification(g, role_doc_id, role_start,
                                                                                role_end, system, arg_confidence)
                        aifutils.add_source_document_to_justification(g, role_justification_arg, doc_id_to_root_dict[role_doc_id])
                        role_justification = aifutils.mark_compound_justification(g, role_asser, [role_justification_trigger, role_justification_arg], system, arg_confidence)
                        # add_filetype(g, role_justification, evt_info[evt_id]['filetype'])

                # add temporal info
                if 'time' in evt_info[evt_id]:
                    dates = evt_info[evt_id]['time']
                    startE = LDCTimeComponent(LDCTimeType.AFTER, dates[0][0], dates[0][1], dates[0][2])
                    startL = LDCTimeComponent(LDCTimeType.BEFORE, dates[1][0], dates[1][1], dates[1][2])
                    endE = LDCTimeComponent(LDCTimeType.AFTER, dates[2][0], dates[2][1], dates[2][2])
                    endL = LDCTimeComponent(LDCTimeType.BEFORE, dates[3][0], dates[3][1], dates[3][2])
                    aifutils.mark_ldc_time_range(g, evt, startE, startL, endE, endL, system)
                
                # # add attributes
                # if 'polarity' in evt_info[evt_id] and evt_info[evt_id]['polarity'] == 'Negative':
                #     aifutils.mark_attribute(g, evt, interchange_ontology.Negated)
                # if 'modality' in evt_info[evt_id] and evt_info[evt_id]['modality'] != 'Asserted':
                #     aifutils.mark_attribute(g, evt, interchange_ontology.Hedged)
                # # aifutils.mark_attribute(g, event, interchange_ontology.Irrealis)
                # if 'genericity' in evt_info[evt_id] and evt_info[evt_id]['genericity'] == 'Generic':
                #     aifutils.mark_attribute(g, evt, interchange_ontology.Generic)
                 
                # # add news source info
                # if source_dict is not None and doc_id in source_dict:
                #     evt_source_system = aifutils.make_system_with_uri(g, "http://www.uiuc.edu/news_source")
                #     aifutils.mark_private_data(g, evt, json.dumps({'news_source': "www."+source_dict[doc_id]+".com"}), evt_source_system)

        # # add event coreference scores
        # if evt_coref_score is not None:
        #     evt_coref_system = aifutils.make_system_with_uri(g, "http://www.uiuc.edu/event_coreference")
        #     for offset1 in evt_coref_score[doc_id]:
        #         evt_coref_json = dict()
        #         if offset1 not in offset_aif:
        #             continue
        #         offset1_aif = offset_aif[offset1]
        #         for offset2 in evt_coref_score[doc_id][offset1]:
        #             score = evt_coref_score[doc_id][offset1][offset2]
        #             if offset2 in offset_aif:
        #                 offset2_aif = offset_aif[offset2]
        #                 evt_coref_json[offset2_aif] = score
        #         evt_coref_str = json.dumps(evt_coref_json)
        #         aifutils.mark_private_data(g, offset1_aif, evt_coref_str, evt_coref_system)

        claim_data_new[doc_id] = list()
        claim_system = aifutils.make_system_with_uri(g, "http://www.uiuc.edu/claim_detection")
        for claim_idx, claim_dict in enumerate(claim_data[doc_id]):
            # find claim results
            claim_id = 'claim_%s_%s' % (doc_id, claim_idx)
            sent_start = claim_dict['start_char']
            sent_end = claim_dict['end_char']
            sentence = claim_dict["sentence"]
            # print('sentence', sent_start, sent_end, sentence)
            # print('-----------')
            claim_x = claim_dict['x_variable']
            claim_x_start = claim_dict['x_variable_start'] + sent_start # claim_dict['x_start'] + sent_start # 
            claim_x_end = claim_dict['x_variable_end'] + sent_start - 1 # claim_dict['x_end'] + sent_start - 1 # 
            # # assert claim_dict['x_variable'] == get_str_from_ltf(doc_id, claim_x_start, claim_x_end, ltf_dir)
            # print('-----------------------')

            claimer_start = claim_dict['claimer_start']
            claimer_end = claim_dict['claimer_end']
            if ("claimer_debug" in claim_dict) and ('extracted_from' in claim_dict["claimer_debug"]):
                if claim_dict["claimer_debug"]["extracted_from"] == "full document" and "full_doc_output" in claim_dict["claimer_debug"]:
                    claimer_start = claim_dict["claimer_debug"]["full_doc_output"]["start"]
                    claimer_end = claim_dict["claimer_debug"]["full_doc_output"]["end"]

            if claim_dict['claim_span_start'] == 0:
                claim_start = sent_start
            else:
                claim_start = claim_dict['claim_span_start'] + sent_start
            if claim_dict['claim_span_end'] == 0:
                claim_end = sent_end
            else:
                claim_end = claim_dict['claim_span_end'] + sent_start - 1
            if claim_end < claim_start:
                claim_end = sent_end
                # print(str(claim_dict))
            if len(claim_dict["claim_span_text"]) > 0:
                claim_text = claim_dict["claim_span_text"]
                # print(doc_id, claim_dict['claim_span_start'], claim_dict['claim_span_end'], claim_dict['claim_span_text'])
                # print('-----------------------')
                # add x_variable to claim span
                if claim_x_start < claim_start:
                    claim_start = claim_x_start
                if claim_x_end > claim_end:
                    claim_end = claim_x_end
                # add claimer to claim span
                if sent_start <= claimer_start and claimer_end <= sent_end:
                    # if claimer is in the sentence, add claimer info into the description
                    if claimer_start < claim_start:
                        claim_start = claimer_start
                    if claimer_end > claim_end:
                        claim_end = claimer_end
                claim_text = get_str_from_ltf(doc_id, claim_start, claim_end, ltf_dir)
            else:
                # no span, use the sentence
                claim_text = sentence
            # print('[final claim text]:', claim_text)
            # print('===================')

            

            claimer_text = claim_dict['claimer_text']
            if 'claimer_qnode' in claim_dict:
                claimer_qnode = claim_dict['claimer_qnode']
            # else:
            #     claimer_qnode = AIDA_namespace.none
            claimer_id = '%s_claimer' % (claim_id)

            claim_dict['associated_KEs'] = list()
            claim_dict['claim_semantics'] = list()
            claim_dict['x_ke'] = list()
            claim_dict['x_ke_qnode'] = list()
            claim_dict['x_ke_typeqnode'] = list()
            claim_dict['claimer_ke'] = list()
            claim_dict['claimer_ke_qnode'] = list()
            claim_dict['claimer_ke_typeqnode'] = list()
            for ke_type in ['event', 'relation']:
                for evt_id in doc_ke[doc_id][ke_type]:
                    if len(evt_args[evt_id]) == 0:
                        continue
                    evt_cluster_uri = "http://www.isi.edu/gaia/clusters/uiuc/%ss/%s/%s" % (ke_type, doc_id, evt_id)
                    # evt_uri = "http://www.isi.edu/gaia/%ss/uiuc/%s/%s" % (ke_type, doc_id, evt_id)
                    evt_type = evt_info[evt_id]['type']
                    for offset in evt_info[evt_id]['mention']:
                        mention_confidence, mention_type, mention_str = evt_info[evt_id]['mention'][offset]
                        doc_id_mention, start_offset, end_offset = parse_offset_str(offset)
                        # add events based on topics
                        for topic_event_type in topic_type_map[claim_dict['sub_topic']]:
                            if evt_type.startswith(topic_event_type):
                                if len(evt_args[evt_id]) > 0:
                                    if sent_start-500 <= start_offset and end_offset <= sent_end+500:
                                        claim_dict['associated_KEs'].append( (evt_id, mention_str, evt_info[evt_id]['type'], offset, evt_cluster_uri, evt_args[evt_id]))
                                        claim_dict['claim_semantics'].append( (evt_id, mention_str, evt_info[evt_id]['type'], offset, evt_cluster_uri, evt_args[evt_id]))
                        # add events based on offset
                        if doc_id_mention == doc_id:
                            if sent_start-200 <= start_offset and end_offset <= sent_end+200:
                                # g.add((CLAIM_namespace[claim_id], AIDA_namespace.associatedKEs, URIRef(evt_cluster_uri) ))
                                claim_dict['associated_KEs'].append( (evt_id, mention_str, evt_info[evt_id]['type'], offset, evt_cluster_uri, evt_args[evt_id]))
                            # if claim_start-1 <= start_offset and end_offset <= claim_end+1:
                            if sent_start-100 <= start_offset and end_offset <= sent_end+100: # use sentence offset, since the claim span may not correct
                                # g.add((CLAIM_namespace[claim_id], AIDA_namespace.claimSemantics, URIRef(evt_cluster_uri) ))
                                claim_dict['claim_semantics'].append( (evt_id, mention_str, evt_info[evt_id]['type'], offset, evt_cluster_uri, evt_args[evt_id]))
            if len(claim_dict['associated_KEs']) == 0:
                for ke_type in ['event', 'relation']:
                    for evt_id in doc_ke[doc_id][ke_type]:
                        if len(evt_args[evt_id]) == 0:
                            continue
                        evt_cluster_uri = "http://www.isi.edu/gaia/clusters/uiuc/%ss/%s/%s" % (ke_type, doc_id, evt_id)
                        # evt_uri = "http://www.isi.edu/gaia/%ss/uiuc/%s/%s" % (ke_type, doc_id, evt_id)
                        evt_type = evt_info[evt_id]['type']
                        for offset in evt_info[evt_id]['mention']:
                            mention_confidence, mention_type, mention_str = evt_info[evt_id]['mention'][offset]
                            doc_id_mention, start_offset, end_offset = parse_offset_str(offset)
                            # add events based on topics
                            for topic_event_type in topic_type_map[claim_dict['sub_topic']]:
                                if evt_type.startswith(topic_event_type):
                                    if len(evt_args[evt_id]) > 0:
                                        if sent_start-900 <= start_offset and end_offset <= sent_end+900:
                                            claim_dict['associated_KEs'].append( (evt_id, mention_str, evt_info[evt_id]['type'], offset, evt_cluster_uri, evt_args[evt_id]))
                                            claim_dict['claim_semantics'].append( (evt_id, mention_str, evt_info[evt_id]['type'], offset, evt_cluster_uri, evt_args[evt_id]))
                            # add events based on offset
                            if doc_id_mention == doc_id:
                                if sent_start-400 <= start_offset and end_offset <= sent_end+400:
                                    # g.add((CLAIM_namespace[claim_id], AIDA_namespace.associatedKEs, URIRef(evt_cluster_uri) ))
                                    claim_dict['associated_KEs'].append( (evt_id, mention_str, evt_info[evt_id]['type'], offset, evt_cluster_uri, evt_args[evt_id]))
                                # if claim_start-1 <= start_offset and end_offset <= claim_end+1:
                                if sent_start-200 <= start_offset and end_offset <= sent_end+200: # use sentence offset, since the claim span may not correct
                                    # g.add((CLAIM_namespace[claim_id], AIDA_namespace.claimSemantics, URIRef(evt_cluster_uri) ))
                                    claim_dict['claim_semantics'].append( (evt_id, mention_str, evt_info[evt_id]['type'], offset, evt_cluster_uri, evt_args[evt_id]))
            for ent_id in doc_ke[doc_id]['entity']:
                ent_uri = "http://www.isi.edu/gaia/entities/uiuc/%s/%s" % (doc_id, ent_id)
                ent_cluster_uri = "http://www.isi.edu/gaia/clusters/uiuc/entity/%s/%s" % (doc_id, ent_id)
                for offset in entity_info[ent_id]['mention']:
                    mention_confidence, mention_type, mention_str = entity_info[ent_id]['mention'][offset]
                    doc_id_mention, start_offset, end_offset = parse_offset_str(offset)
                    if doc_id_mention == doc_id:
                        # if 'covid' in mention_str.lower():
                        #     claim_dict['associated_KEs'].append( (ent_id, mention_str, entity_info[ent_id]['type'], offset, ent_cluster_uri, "") )
                        #     claim_dict['claim_semantics'].append( (ent_id, mention_str, entity_info[ent_id]['type'], offset, ent_cluster_uri, "") )
                        
                        # associated_KEs
                        if sent_start-10 <= start_offset and end_offset <= sent_end+10:
                            # g.add((CLAIM_namespace[claim_id], AIDA_namespace.associatedKEs, URIRef(ent_cluster_uri) ))
                            claim_dict['associated_KEs'].append( (ent_id, mention_str, entity_info[ent_id]['type'], offset, ent_cluster_uri, "") )
                        # claim_semantics
                        if claim_start-1 <= start_offset and end_offset <= claim_end+1:
                            # remove claimer
                            if (claimer_start <= start_offset and end_offset <= claimer_end) or ( start_offset <= claimer_start and claimer_end <= end_offset): # offset overlap
                                # remove claimer from the claim semantics
                                continue
                            else:
                                # g.add((CLAIM_namespace[claim_id], AIDA_namespace.claimSemantics, URIRef(ent_cluster_uri) ))
                                claim_dict['claim_semantics'].append( (ent_id, mention_str, entity_info[ent_id]['type'], offset, ent_cluster_uri, "") )
                        # x
                        if (claim_x_start <= start_offset and end_offset <= claim_x_end) or ( start_offset <= claim_x_start and claim_x_end <= end_offset): # offset overlap
                            claim_dict['x_ke'].append( (ent_id, mention_str, offset, ent_uri) )
                            if 'link' in entity_info[ent_id]:
                                claim_dict['x_ke_qnode'].extend(entity_info[ent_id]['link'].keys())
                            if 'type_qnode' in entity_info[ent_id]:
                                claim_dict['x_ke_typeqnode'].extend(entity_info[ent_id]['type_qnode'].keys())
                            # add to claim semantics
                            claim_dict['claim_semantics'].append( (ent_id, mention_str, entity_info[ent_id]['type'], offset, ent_cluster_uri, "") )
                        # claimer
                        if (claimer_start <= start_offset and end_offset <= claimer_end) or ( start_offset <= claimer_start and claimer_end <= end_offset): # offset overlap
                            claim_dict['claimer_ke'].append( (ent_id, mention_str, offset, ent_uri) )
                            claim_dict['claimer_ke_qnode'].extend(entity_info[ent_id]['link'].keys())
                            claim_dict['claimer_ke_typeqnode'].extend(entity_info[ent_id]['type_qnode'].keys())
            # if len(claim_dict['associated_KEs']) == 0:
            #     # if no associated_KEs, extend the span of the claim:
            #     for ent_id in doc_ke[doc_id]['entity']:
            #         ent_uri = "http://www.isi.edu/gaia/entities/uiuc/%s/%s" % (doc_id, ent_id)
            #         ent_cluster_uri = "http://www.isi.edu/gaia/clusters/uiuc/entity/%s/%s" % (doc_id, ent_id)
            #         for offset in entity_info[ent_id]['mention']:
            #             mention_confidence, mention_type, mention_str = entity_info[ent_id]['mention'][offset]
            #             doc_id_mention, start_offset, end_offset = parse_offset_str(offset)
            #             if doc_id_mention == doc_id:
            #                 # associated_KEs
            #                 if sent_start-450 <= start_offset and end_offset <= sent_end+450:
            #                     # g.add((CLAIM_namespace[claim_id], AIDA_namespace.associatedKEs, URIRef(ent_cluster_uri) ))
            #                     claim_dict['associated_KEs'].append( (ent_id, mention_str, entity_info[ent_id]['type'], offset, ent_cluster_uri, "") )
            #                 # claim_semantics
            #                 if claim_start-250 <= start_offset and end_offset <= claim_end+250:
            #                     # remove claimer
            #                     if (claimer_start <= start_offset and end_offset <= claimer_end) or ( start_offset <= claimer_start and claimer_end <= end_offset): # offset overlap
            #                         # remove claimer from the claim semantics
            #                         continue
            #                     else:
            #                         # g.add((CLAIM_namespace[claim_id], AIDA_namespace.claimSemantics, URIRef(ent_cluster_uri) ))
            #                         claim_dict['claim_semantics'].append( (ent_id, mention_str, entity_info[ent_id]['type'], offset, ent_cluster_uri, "") )
            
            # add arguments
            for evt_id, _, _, _, _, _ in claim_dict['associated_KEs']:
                if 'Event' in evt_id:
                    for role in evt_args[evt_id]:
                        for arg_id in evt_args[evt_id][role]:
                            saved = False
                            for ent_id, _, _, _, _, _ in claim_dict['associated_KEs']:
                                if arg_id == ent_id:
                                    saved = True
                                    break
                            if saved:
                                continue
                            trigger_arg_offset, arg_offset, arg_confidence = evt_args[evt_id][role][arg_id][0]
                            arg_uri = "http://www.isi.edu/gaia/entities/uiuc/%s/%s" % (doc_id, arg_id)
                            arg_cluster_uri = "http://www.isi.edu/gaia/clusters/uiuc/entity/%s/%s" % (doc_id, arg_id)
                            doc_id_mention, start_offset, end_offset = parse_offset_str(arg_offset)
                            if doc_id_mention == doc_id:
                                claim_dict['associated_KEs'].append( (arg_id, entity_info[arg_id]['canonical_mention'][doc_id][0], entity_info[arg_id]['type'], arg_offset, arg_cluster_uri, "") )
            for evt_id, _, _, _, _, _ in claim_dict['claim_semantics']:
                if 'Event' in evt_id:
                    for role in evt_args[evt_id]:
                        for arg_id in evt_args[evt_id][role]:
                            saved = False
                            for ent_id, _, _, _, _, _ in claim_dict['claim_semantics']:
                                if arg_id == ent_id:
                                    saved = True
                                    break
                            if saved:
                                continue
                            trigger_arg_offset, arg_offset, arg_confidence = evt_args[evt_id][role][arg_id][0]
                            arg_uri = "http://www.isi.edu/gaia/entities/uiuc/%s/%s" % (doc_id, arg_id)
                            arg_cluster_uri = "http://www.isi.edu/gaia/clusters/uiuc/entity/%s/%s" % (doc_id, arg_id)
                            doc_id_mention, start_offset, end_offset = parse_offset_str(arg_offset)
                            if doc_id_mention == doc_id:
                                claim_dict['claim_semantics'].append( (arg_id, entity_info[arg_id]['canonical_mention'][doc_id][0], entity_info[arg_id]['type'], arg_offset, arg_cluster_uri, "") )

            if len(claim_dict['claim_semantics']) == 0:
                # if no semantics is extracted, add all the possible KEs from associated_KEs
                claim_dict['claim_semantics'] = claim_dict['associated_KEs']
            if len(claim_dict['x_ke_qnode']) == 0:
                if claim_x in qnode_dict:
                    claim_dict['x_ke_qnode'].append(qnode_dict[claim_x]['qnode'].most_common()[0][0])
            if len(claim_dict['x_ke_typeqnode']) == 0:
                if claim_x in qnode_dict:
                    claim_dict['x_ke_typeqnode'].extend(qnode_dict[claim_x]['type_qnode'].keys())
            if len(claim_dict['claimer_ke_qnode']) == 0:
                if claimer_text in qnode_dict:
                    claim_dict['claimer_ke_qnode'].append(qnode_dict[claimer_text]['qnode'].most_common()[0][0])
            if len(claim_dict['claimer_ke_typeqnode']) == 0:
                if claimer_text in qnode_dict:
                    claim_dict['claimer_ke_typeqnode'].extend(qnode_dict[claimer_text]['type_qnode'].keys())
            # print(len(claim_dict['x_ke_qnode']), len(claim_dict['claimer_ke_qnode']))
            claim_dict['claim_id'] = claim_id
            # add template
            # max_topic_ = ''
            # max_topic_score_ = 0.0
            # for topic_ in claim_dict['topic_scores']:
            #     topic_score_ = claim_dict['topic_scores'][topic_]['score']
            #     if max_topic_score_ < topic_score_:
            #         max_topic_score_ = topic_score_
            #         max_topic_ = topic_
            # claim_dict['subtopic'] = claim_dict['sub_topic'] #template[max_topic_][1]
            # claim_dict['template'] = claim_dict['template'] #template[max_topic_][2]
            claim_dict['topic_score'] = float(claim_dict['final_claim_score'])
            

            # must have knowledge elements
            if len(claim_dict['claim_semantics']) == 0 or len(claim_dict['associated_KEs']) == 0:
                continue

            claim_topic = claim_dict['topic']
            claim_confidence = float(claim_dict['claimbuster_score'])
            

            claimObject = claim.Claim()
            claimObject.importance = claim_confidence
            claimObject.claimId = claim_id
            # claimObject.queryId = "QueryId:1776"
            if 'template' in claim_dict:
                claimObject.claimTemplate = claim_dict['template']
            elif 'subtopic_question' in claim_dict:
                claimObject.claimTemplate = claim_dict['subtopic_question']
            claimObject.naturalLanguageDescription = claim_text
            # g.add((CLAIM_namespace[claim_id], AIDA_namespace.claimText, Literal(claim_text, datatype=XSD.string) ))
            claimObject.topic = claim_topic
            claimObject.subtopic = claim_dict['sub_topic']
            claimObject.sourceDocument = root_doc_id
            new_claim_start, new_claim_end = transoffset_mapping(doc_id, claim_start, claim_end, translation_mapping)
            justification_aif = aifutils.mark_text_justification(g, [CLAIM_namespace[claim_id]], doc_id, new_claim_start,
                                                                                    new_claim_end, claim_system, claim_confidence)
            justification_aif = aifutils.add_source_document_to_justification(g, justification_aif, root_doc_id)
            # print('doc_id, claim_start, claim_end', doc_id, claim_start, claim_end)
            sentence_before, sent, sentence_after = get_context_sentences(doc_id, claim_start, claim_end, ltf_dir)
            # print('sentence', sentence)
            # print('sent', sent)
            assert sentence == sent
            aifutils.mark_private_data(g, justification_aif, json.dumps({
                'final_claim_score': claim_dict['topic_score'],
                'source':doc_id, 
                'sourceDocument':root_doc_id, 'startOffset_translation': claim_start, 'endOffsetInclusive_translation': claim_end,
                'startOffset': new_claim_start, 'endOffsetInclusive': new_claim_end,
                'sentence':sentence, 
                'sentence_before': sentence_before, 
                'sentence_after': sentence_after, 
                }), claim_system)
            
            
            if 'qnode_x_variable_identity' in claim_dict:
                claim_x_qnode = claim_dict['qnode_x_variable_identity']
            # else:
            #     claim_x_qnode = AIDA_namespace.none
            # if 'qnode_x_variable_type' in claim_dict:
            #     claim_x_qnode_type = claim_dict['qnode_x_variable_type']
            # else:
            #     claim_x_qnode_type = AIDA_namespace.none
            x_varible_id = '%s_X' % (claim_id)
            x_var_component                = claim_component.ClaimComponent()
            x_var_component.setName        = claim_x
            if only_qnode:
                x_var_component.setIdentity= claim_dict['qnode_x_variable_identity']
            else:
                if len(claim_dict['x_ke_qnode']) > 0:
                    x_var_component.setIdentity= claim_dict['x_ke_qnode'][0] #entity_info[x_varible_ke]['link']
                else:
                    x_var_component.setIdentity= claim_x_qnode
            # if only_qnode:
            #     x_var_component.addType    = claim_dict['qnode_x_variable_type']
            # else:
            #     for type_node_ in claim_dict['x_ke_typeqnode']:
            #         x_var_component.addType    = type_node_ #entity_info[x_varible_ke]['type_qnode']
            #     if 'qnode_x_variable_type' in claim_dict:
            #         x_var_component.addType    = claim_dict['qnode_x_variable_type']
            x_typenodes = set()
            if claim_x.lower() in qnode_dict['entity']:
                # if can directly matched to xpo, use the type from xpo
                x_type_qnode_dict = qnode_dict['entity'][claim_x.lower()]
                # if it is same as identity qnode, exclude it
                if x_type_qnode_dict != claim_dict['qnode_x_variable_identity']:
                    x_var_component.addType   = x_type_qnode_dict
                    x_typenodes.add(x_type_qnode_dict)
            # if len(x_typenodes) == 0:
            #     # otherwise cannot be mapped using the xpo names, use Tuan's result
            x_var_component.addType   = claim_dict['qnode_x_variable_type'] # always have Tuan's type Qnode?
            # get all possible type nodes
            x_typenodes.add(claim_dict['qnode_x_variable_type'])
            for type_node_ in claim_dict['x_ke_typeqnode']:
                x_typenodes.add(type_node_ )        
            x_var_component.setProvenance  = sentence
            if len(claim_dict['x_ke']) > 0:
                x_varible_ke = URIRef(claim_dict['x_ke'][-1][3])
                x_var_component.setKe          = x_varible_ke
            x_var_component_aif = aifutils.make_claim_component(g, (CLAIM_namespace[x_varible_id]), x_var_component, claim_system)
            claimObject.addXVariable = x_var_component_aif
            aifutils.mark_private_data(g, x_var_component_aif, json.dumps({
                'x_variable_type_qnode': list(x_typenodes), 
                # 'topic_confidence':claim_dict['topic_scores'], 
                'claimbuster_score': claim_dict['claimbuster_score'], 
                'final_claim_score': claim_dict['final_claim_score'],
                'claimer_score': claim_dict['claimer_debug']['score'],  # claim_dict['claimer_debug']['sent_output']['score'], # 
                'sentence':sentence, 
                'source':doc_id, 
                'sourceDocument':root_doc_id, 'startOffset': claim_start, 'endOffsetInclusive': claim_end
                }), claim_system)
            

            
            claimer_component                = claim_component.ClaimComponent()
            claimer_component.setName        = claimer_text
            if only_qnode:
                claimer_component.setIdentity = claim_dict['claimer_qnode']
            else:
                if len(claim_dict['claimer_ke_qnode']) > 0:
                    claimer_component.setIdentity    = claim_dict['claimer_ke_qnode'][0] #entity_info[claimer_ke]['link']
                else:
                    claimer_component.setIdentity    = claimer_qnode
            # if only_qnode:
            #     claimer_component.addType    = claim_dict['claimer_type_qnode']
            # else:
            #     for type_node_ in claim_dict['claimer_ke_typeqnode']:
            #         claimer_component.addType    = type_node_ 
            #     if 'claimer_type_qnode' in claim_dict:
            #         claimer_component.addType    = claim_dict['claimer_type_qnode']
            claimer_typenodes = set()
            if claimer_text.lower() in qnode_dict['entity']:
                # if can directly matched to xpo, use the type from xpo
                claimer_type_qnode_dict = qnode_dict['entity'][claimer_text.lower()]
                # if it is same as identity qnode, exclude it
                if claimer_type_qnode_dict != claim_dict['claimer_qnode']:
                    claimer_component.addType   = claimer_type_qnode_dict
                    claimer_typenodes.add(claimer_type_qnode_dict)
            # if len(claimer_typenodes) == 0:
            #     # otherwise cannot be mapped using the xpo names, use Tuan's result
            claimer_component.addType   = claim_dict['claimer_type_qnode'] # always have Tuan's type Qnode?
            # get all possible type nodes
            claimer_typenodes.add(claim_dict['claimer_type_qnode'])
            for type_node_ in claim_dict['claimer_ke_typeqnode']:
                claimer_typenodes.add(type_node_ )        
            
            claimer_component.setProvenance  = sentence
            if len(claim_dict['claimer_ke']) > 0:
                claimer_ke = URIRef(claim_dict['claimer_ke'][-1][3])
                claimer_component.setKe          = claimer_ke
                if 'affiliation' in entity_info[claim_dict['claimer_ke'][-1][0]]:
                    affiliation_entid, affiliation_offset = entity_info[claim_dict['claimer_ke'][-1][0]]['affiliation']
                    # if doc_id in entity_info[affiliation_entid]['canonical_mention']:
                    # print('affiliation_entid', affiliation_entid)
                    if affiliation_entid in doc_ke[doc_id]['entity']:
                        affiliation_entid_mention, affiliation_mention_offset = entity_info[affiliation_entid]['canonical_mention'][doc_id]
                        # print('yes')
                        affiliation_component                = claim_component.ClaimComponent()
                        affiliation_component.setName        = affiliation_entid_mention
                        claim_dict['claimer_affiliation']    = affiliation_entid_mention
                        # affiliation_component.setName        = entity_info[affiliation_entid]['name'][0]
                        affiliation_component.setIdentity    = list(entity_info[affiliation_entid]['link'].keys())[0]
                        claim_dict['claimer_affiliation_identity_qnode']    = list(entity_info[affiliation_entid]['link'].keys())[0]
                        affiliation_component.addType        = list(entity_info[affiliation_entid]['type_qnode'].keys())[0]
                        claim_dict['claimer_affiliation_type_qnode']    = list(entity_info[affiliation_entid]['type_qnode'].keys())[0]
                        affiliation_doc_id, affiliation_start, affiliation_end = parse_offset_str(affiliation_mention_offset)
                        affiliation_component.setProvenance  = get_str_from_ltf(affiliation_doc_id, affiliation_start, affiliation_end, ltf_dir)
                        affiliation_component.setKe          = URIRef("http://www.isi.edu/gaia/entities/uiuc/%s/%s" % (affiliation_doc_id, affiliation_entid))
                        affiliation_component_aif = aifutils.make_claim_component(g, CLAIM_namespace['%s_claimer_affiliation' % claim_id], affiliation_component, claim_system)
                        claimObject.addClaimerAffiliation = affiliation_component_aif
            claimer_component_aif = aifutils.make_claim_component(g, CLAIM_namespace[claimer_id], claimer_component, claim_system)
            claimObject.claimer = claimer_component_aif
            aifutils.mark_private_data(g, claimer_component_aif, json.dumps({
                'claimer_type_qnode':list(claimer_typenodes), 
                'claimer_score': claim_dict['claimer_debug']['score'] # claim_dict['claimer_debug']['sent_output']['score'] # 
                }
            ), 
            claim_system) 
            
            
            # claimObject.claimMedium = validMediumClaimComponent

            related_events = set()
            for ent_id, mention_str, ent_type, offset, ent_uri, evt_arg_gooboor in claim_dict['associated_KEs']:
                claimObject.addAssociatedKE = URIRef(ent_uri)
                if 'Event' in ent_id:
                    related_events.add(ent_id)
            for ent_id, mention_str, ent_type, offset, ent_uri, evt_arg_gooboor  in claim_dict['claim_semantics']:
                claimObject.addClaimSemantics = URIRef(ent_uri)
           
            claimObject.sentiment = interchange_ontology.SentimentNeutralUnknown
            claimObject.epistemic =  interchange_ontology.EpistemicUnknown

            locations = Counter()
            for evt_id in related_events:
                if 'Place' in evt_args[evt_id]:
                    for arg_id in evt_args[evt_id]['Place']:
                        if arg_id in doc_ke[doc_id]['entity'] or arg_id in doc_ke[doc_id]['event']:
                            trigger_arg_offset, arg_offset, arg_confidence = evt_args[evt_id]['Place'][arg_id][0]
                            locations[arg_id] += 1
            if len(locations) > 0:
                arg_id = locations.most_common()[0][0]
                arg_mention, arg_canmention_offset = entity_info[arg_id]['canonical_mention'][doc_id]
                location_component                = claim_component.ClaimComponent()
                location_component.setName        = arg_mention
                claim_dict['location']            = arg_mention
                # location_component.setName        = entity_info[arg_id]['name'][0]
                location_component.setIdentity    = list(entity_info[arg_id]['link'].keys())[0]
                claim_dict['location_identity_qnode']            = list(entity_info[arg_id]['link'].keys())[0]
                location_component.addType        = list(entity_info[arg_id]['type_qnode'].keys())[0]
                claim_dict['location_type_qnode']            = list(entity_info[arg_id]['type_qnode'].keys())[0]
                location_component.setProvenance  = sentence
                location_component.setKe          = URIRef("http://www.isi.edu/gaia/entities/uiuc/%s/%s" % (doc_id, arg_id))
                            
                location_component_aif = aifutils.make_claim_component(g, CLAIM_namespace['%s_claim_location' % claim_id], location_component, claim_system)
                claimObject.claimLocation = location_component_aif

            times_0, times_1, times_2, times_3 = Counter(), Counter(), Counter(), Counter()
            for evt_id in related_events:
                # startE = LDCTimeComponent(LDCTimeType.AFTER, None, None, None)
                # startL = LDCTimeComponent(LDCTimeType.BEFORE, None, None, None)
                # endE = LDCTimeComponent(LDCTimeType.AFTER, None, None, None)
                # endL = LDCTimeComponent(LDCTimeType.BEFORE, None, None, None)
                # #LDCTimeComponent
                if 'time' in evt_info[evt_id]:
                    dates = evt_info[evt_id]['time']
                    if dates[0] is not None:
                        times_0[dates[0]] += 1
                    if dates[1][0] is not None:
                        times_1[dates[1]] += 1
                    if dates[2][0] is not None:
                        times_2[dates[2]] += 1
                    if dates[3][0] is not None:
                        times_3[dates[3]] += 1
                if len(times_0) > 0:
                    time_0 = times_0.most_common()[0][0]
                    startE = LDCTimeComponent(LDCTimeType.AFTER, time_0[0], time_0[1], time_0[2])
                    claim_dict['time_start_earliest'] = startE
                if len(times_1) > 0:
                    time_1 = times_1.most_common()[0][0]
                    startL = LDCTimeComponent(LDCTimeType.BEFORE, time_1[0], time_1[1], time_1[2])
                    claim_dict['time_start_latest'] = startL
                if len(times_2) > 0:
                    time_2 = times_2.most_common()[0][0]
                    endE = LDCTimeComponent(LDCTimeType.AFTER, time_2[0], time_2[1], time_2[2])
                    claim_dict['time_end_earliest'] = endE
                if len(times_3) > 0:
                    time_3 = times_3.most_common()[0][0]
                    # setting end_before = start_after if end_before < start_after.
                    if len(times_0) > 0:
                        if '%s-%s-%s' % (time_3[0], time_3[1], time_3[2]) < '%s-%s-%s' % (time_0[0], time_0[1], time_0[2]):
                            time_3 = time_0
                    endL = LDCTimeComponent(LDCTimeType.BEFORE, time_3[0], time_3[1], time_3[2])
                    claim_dict['time_end_latest'] = endL
                claimObject.claimDateTime = aifutils.make_ldc_time_range(g, startE, startL, endE, endL, claim_system)
                
            aifutils.make_claim(g, CLAIM_namespace[claim_id], claimObject, claim_system)

            # update JSON
            claim_data_new[doc_id].append(claim_dict)
            

        g.serialize(destination=os.path.join(output_ttl_dir, root_doc_id+'.ttl'), format='ttl')

        # break

    json.dump(claim_data_new, open(os.path.join(output_ttl_dir, 'claim_all.json'), 'w'), indent=4)
    # statistics_claim(claim_data_new)




if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Final output to ColdStart++ including all components')
    parser.add_argument("--input_cs", help="input CS file", required=True)
    parser.add_argument('--ltf_dir', help='ltf_dir', required=True)
    parser.add_argument('--output_ttl_dir', help='output_ttl_dir', required=True)
    parser.add_argument('--language', default='en', help='language_mediatype', required=True)
    parser.add_argument('--validate_offset', action='store_true', help='whether validate the offset using ltf', required=False)
    parser.add_argument('--eval', default='m36', type=str, help='evaluation', required=False)
    
    parser.add_argument('--overlay', default='params/xpo_v3.1.json', type=str, help='xpo_overlay_json', required=True)
    parser.add_argument('--evt_coref_score_tab', type=str, help='adding event coreference scores into private data', required=False)
    parser.add_argument('--source_tab', type=str, default=None, help='adding source info to show news agency', required=False)
    # parser.add_argument('--source_tab_context', type=str, help='adding source info to show news agency', required=False)
    parser.add_argument('--single_type', default=False, action='store_true', help='only keeps one type for each entity', required=False)
    parser.add_argument('--event_embedding_from_file', default=False, action='store_true',
                        help='append event embedding from OneIE')
    parser.add_argument('--ent_vec_dir', default=None, type=str, 
                        help='ent_vec_dir')
    parser.add_argument('--ent_vec_files', default=None, nargs='+', type=str,
                        help='ent_vec_files')
    parser.add_argument('--evt_vec_dir', default=None, type=str, 
                        help='evt_vec_dir')
    parser.add_argument('--evt_vec_files', default=None, nargs='+', type=str,
                        help='evt_vec_files')
    parser.add_argument('--freebase_tab', default=None, type=str, help='%s.linking.freebase.tab')
    parser.add_argument('--fine_grained_entity_type_path', type=str,
                        help='%s.linking.freebase.fine.json')
    parser.add_argument('--lorelei_link_mapping', type=str,
                        help='edl/lorelei_private_data.json')
    parser.add_argument('--parent_child_tab_path', type=str, default=None,
                        help='parent_child_tab_path')
    parser.add_argument('--claim_json', type=str, default=None, required=True,
                        help='claim json')
    parser.add_argument('--trans_json', type=str, default=None, required=False,
                        help='trans2raw json')
    parser.add_argument('--str_mapping_file', type=str, default=None, required=False,
                        help='string translation mapping txt')
    

    args = parser.parse_args()

    input_cs = args.input_cs
    ltf_dir = args.ltf_dir
    output_ttl_dir = args.output_ttl_dir
    language = args.language
    validate_offset = args.validate_offset
    overlay = args.overlay
    evt_coref_score_tab = args.evt_coref_score_tab
    source_tab = args.source_tab
    # source_tab_context =args.source_tab_context
    single_type = args.single_type
    if not os.path.exists(output_ttl_dir):
        os.makedirs(output_ttl_dir)
    event_embedding_from_file=args.event_embedding_from_file
    ent_vec_dir = args.ent_vec_dir
    ent_vec_files = args.ent_vec_files
    evt_vec_dir = args.evt_vec_dir
    evt_vec_files = args.evt_vec_files
    freebase_tab = args.freebase_tab
    fine_grained_entity_type_path = args.fine_grained_entity_type_path
    parent_child_tab_path = args.parent_child_tab_path
    trans_json = args.trans_json
    str_mapping_file = args.str_mapping_file
    

    # AIDA = Namespace('https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#')
    # RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    # XSD = Namespace('http://www.w3.org/2001/XMLSchema#')
    # LDC = Namespace(prefix_ldc[args.eval])
    # LDC_uri = URIRef(prefix_ldc[args.eval])
    SKOS = ClosedNamespace(uri=URIRef('http://www.w3.org/2004/02/skos/core#'), terms=['prefLabel'])
    
    ontology_data, qnode_name_dict = load_xpo(args.overlay)
    if trans_json is None:
        translation_mapping = None
        str_mapping = None
    else:
        if os.path.exists(trans_json):
            translation_mapping = json.load(open(trans_json))
            str_mapping = get_translation_mapping(str_mapping_file)
        else:
            translation_mapping = None
            str_mapping = None
    doc_ke, entity_info, evt_info, evt_args, evt_args_qnode, qnode_dict = load_cs(input_cs, ontology_data, qnode_name_dict, language, validate_offset, single_type=single_type)
    dirname = os.path.dirname(input_cs)
    json.dump(doc_ke, open(os.path.join(dirname, 'doc_ke.json'), 'w'), indent=4)
    json.dump(entity_info, open(os.path.join(dirname, 'entity_info.json'), 'w'), indent=4)
    json.dump(evt_info, open(os.path.join(dirname, 'evt_info.json'), 'w'), indent=4)
    json.dump(evt_args, open(os.path.join(dirname, 'evt_args.json'), 'w'), indent=4)

    claim_data = load_claim_json(args.claim_json)

    if parent_child_tab_path is not None and os.path.exists(parent_child_tab_path):
        doc_id_to_root_dict = load_doc_root_mapping(parent_child_tab_path)
    else:
        doc_id_to_root_dict = None
    if evt_coref_score_tab is not None and os.path.exists(evt_coref_score_tab):
        evt_coref_score = load_event_coreference_score(evt_coref_score_tab)
    else:
        evt_coref_score = None
    if source_tab is not None and os.path.exists(source_tab):
        source_dict = load_source_tab(source_tab)
    else:
        source_dict = None
    # if source_tab_context is not None and os.path.exists(source_tab_context):
    #     source_dict_columbia = load_source_tab_context(source_tab_context)
    # else:
    #     source_dict_columbia = None
    # if args.event_embedding_from_file:
    #     eng_elmo = None
    #     ukr_elmo = None
    #     rus_elmo = None
    #     offset_event_vec = load_entity_vec(evt_vec_files, evt_vec_dir)
    # else:
    #     eng_elmo = elmoformanylangs.Embedder('/postprocessing/ELMoForManyLangs/eng.model')
    #     ukr_elmo = elmoformanylangs.Embedder('/postprocessing/ELMoForManyLangs/ukr.model')
    #     rus_elmo = elmoformanylangs.Embedder('/postprocessing/ELMoForManyLangs/rus.model')
    #     offset_event_vec = None
    if freebase_tab is not None:
        freebase_links = load_freebase(freebase_tab, input_cs)
    else:
        freebase_links = None
    if fine_grained_entity_type_path is not None:
        fine_grained_entity_dict = json.load(open(fine_grained_entity_type_path))
    else:
        fine_grained_entity_dict = None
    # if lorelei_link_mapping is not None:
    #     lorelei_links = json.load(open(lorelei_link_mapping))
    # else:
    #     lorelei_links = None
    # offset_entity_corefer = load_corefer(edl_tab)
    # offset_entity_vec = load_entity_vec(ent_vec_files, ent_vec_dir)
    offset_entity_vec=None
    offset_event_vec=None
    eng_elmo=None
    ukr_elmo = None
    rus_elmo = None

    gen_ttl(claim_data, doc_ke, entity_info, evt_info, evt_args, evt_args_qnode, qnode_dict, SKOS, output_ttl_dir, evt_coref_score=evt_coref_score, source_dict=source_dict, freebase_links=freebase_links, fine_grained_entity_dict=fine_grained_entity_dict, # lorelei_links=lorelei_links, 
            offset_event_vec=offset_event_vec, offset_entity_vec=offset_entity_vec, doc_id_to_root_dict=doc_id_to_root_dict, ltf_dir=ltf_dir, event_embedding_from_file=event_embedding_from_file, eng_elmo=eng_elmo, ukr_elmo=ukr_elmo, rus_elmo=rus_elmo,
            translation_mapping=translation_mapping, str_mapping=str_mapping, only_qnode=True)
