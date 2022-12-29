import json
import os
import nltk
import math
import re

from nltk.tokenize import sent_tokenize
from nltk.tokenize import TreebankWordTokenizer
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "transition-amr-parser-master"))
from transition_amr_parser.stack_transformer_amr_parser import AMRParser
from typing import List, Tuple
from dataclasses import dataclass

node_line = re.compile(r'# ::node\t(\d+)\t(\S+)\t(\d+)-(\d+)')
root_line = re.compile(r'# ::root\t(\d+)\t(\S+)')
edge_line = re.compile(r'# ::edge\t(\S+)\t(\S+)\t(\S+)\t(\d+)\t(\d+)')
op_through = re.compile(r'^op\d+')
arg1_through = re.compile(r'^ARG1')
arg0_through = re.compile(r'^ARG0')
loc_through = re.compile(r'^location')

# nltk.download('averaged_perceptron_tagger')
# nltk.download('universal_tagset')

@dataclass
class Node:
    start:int
    end:int
    name:str
    text:str
    id:int

@dataclass
class Edge:
    id1: int
    id2: int
    rel: str
    def reverse(self,):
        if self.rel.endswith("-of"):
            self.rel = self.rel[:-3]
            self.id1, self.id2 = self.id2, self.id1

@dataclass
class Graph:
    nodes: List[Node]
    edges: List[Edge]
    sorted:bool = False
    root:int = -1

    def sort_node(self, merge_same_span:bool=False, reverse_edge:bool=False):
        new_nodes = []
        node_mapping = {}
        span_id = {}
        for id_, node in enumerate(self.nodes):
            # print(node)
            if merge_same_span:
                if (node.start, node.end) not in span_id:
                    span_id[(node.start, node.end)] = len(new_nodes)
                    node_mapping[node.id] = len(new_nodes)
                    new_nodes.append(Node(node.start, node.end, node.name, node.text, len(new_nodes)))
                else:
                    node_mapping[node.id] = span_id[(node.start, node.end)]
            else:
                new_nodes.append(Node(node.start, node.end, node.name, node.text, id_))
                node_mapping[node.id] = id_

        new_edges = []
        for edge in self.edges:
            if edge.id1 not in node_mapping or edge.id2 not in node_mapping:
                continue
            if (not merge_same_span) or (node_mapping[edge.id1] != node_mapping[edge.id2]):
                new_edges.append(Edge(node_mapping[edge.id1], node_mapping[edge.id2], edge.rel))
        # for edge in new_edges:
        #     print(edge)
        self.nodes = new_nodes
        self.edges = []
        if reverse_edge:
            for edge in new_edges:
                if edge.rel.endswith("-of") and edge.rel.startswith("ARG"):
                    nedge=Edge(edge.id2, edge.id1, edge.rel[:-3])
                    self.edges.append(nedge)
                else:
                    # print(edge.rel)
                    if edge.rel != "poss" and edge.rel != "part" and edge.rel != "prep-with":
                        # print(edge.rel)
                        self.edges.append(edge)
        self.sorted = True
    def merge_edge(self,):
        for edge in self.edges:
            if op_through.match(edge.rel) is not None:
                new_edges = [Edge(_edge.id1, edge.id2, _edge.rel) for _edge in self.edges if _edge.id2 == edge.id1]
                self.edges.extend(new_edges)
            if arg1_through.match(edge.rel) is not None:
                new_edges = [Edge(_edge.id1, edge.id2, _edge.rel) for _edge in self.edges \
                    if _edge.id2 == edge.id1 and arg1_through.match(_edge.rel) is not None]
                    # A, arg1, B & B arg1 C -> A arg1 C
                new_edges = [Edge(edge.id2, _edge.id2, _edge.rel) for _edge in self.edges \
                    if _edge.id1 == edge.id1 and arg0_through.match(_edge.rel) is not None]
                    # A, arg1, B & A arg0 C -> B arg0 C
                new_edges += [Edge(edge.id1, _edge.id2, _edge.rel) for _edge in self.edges \
                    if _edge.id1 == edge.id2 and loc_through.match(_edge.rel) is not None]
                    # A, arg1, B & B loc C -> A loc C
                self.edges.extend(new_edges)


''' AMR Parsing functions'''


def amr_parsing_sents(parser, tokenizer, granu, input_dir):
    with open(input_dir, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    dicts = [json.loads(line) for line in lines]
    data_num = len(dicts)

    sents, line_id_list = [], []
    for i,data_dict in enumerate(dicts):
        if len(data_dict["annotations"]) != 0:
            sents.append(data_dict["tokens"])
            line_id_list.append(i)

    tokens = [tokenizer.tokenize(sent) for sent in sents]
    spans = [list(tokenizer.span_tokenize(sent)) for sent in sents]
    sent_num = len(sents)

    num_pieces = sent_num // granu + 1
    amrs = ['# ::tok I love you . <ROOT>\n# ::node\t1\ti\t0-1\n# ::node\t2\tlove-01\t1-2\n# ::node\t3\tyou\t2-3\n# ::root\t2\tlove-01\n# ::edge\tlove-01\tARG0\ti\t2\t1\t\n# ::edge\tlove-01\tARG1\tyou\t2\t3\t\n(l / love-01\n      :ARG0 (i / i)\n      :ARG1 (y / you))\n\n' for _ in range(data_num)]

    wrong_ids = []

    for i in range(num_pieces):
        start_id = i * granu
        end_id = (i+1) * granu

        input_tokens = tokens[start_id: end_id]
        try:
            output_amrs = parser.parse_sentences(input_tokens)
            for j,amr_string in enumerate(output_amrs):
                pos = line_id_list[start_id + j]
                amrs[pos] = amr_string
        except:
            wrong_ids.append(i)
    
    for idx in wrong_ids:
        start_id = idx * granu
        end_id = (idx+1) * granu
        input_tokens = tokens[start_id: end_id]
        for j,tokens_j in enumerate(input_tokens):
            try:
                output_amr = parser.parse_sentences([tokens_j])[0]
                pos = line_id_list[start_id + j]
                amrs[pos] = output_amr
            except:
                pass

    return amrs


def amr_parse_file(input_json_dir):
    parser = AMRParser.from_checkpoint('./amr_model/checkpoint_best.pt')
    t = TreebankWordTokenizer()
    amrs = amr_parsing_sents(parser, t, 500, input_json_dir)
    return amrs


''' Argument Extraction Functions'''


def sent_tokenize(sent, tokenizer):
    spans = tokenizer.span_tokenize(sent)
    span_list, tokens_list = [], []
    for t in spans:
        span_list.append(t)
        tokens_list.append(sent[t[0]:t[1]])
    return span_list, tokens_list


def align(input_span_list, span):
    # sent: list of tuples
    span_list = input_span_list.copy()
    span_num = len(span_list)
    span_list.append((span_list[span_num-1][1]+1, math.inf))
    have_start, have_end = False, False
    for i in range(span_num):
        if span_list[i][0] <= span[0] and span_list[i+1][0] > span[0]:
            start = i
            have_start = True
        if span_list[i][1] < span[1] and span_list[i+1][1] >= span[1]:
            end = i+2
            have_end = True

    if have_end and have_start:
        return start, end
    else:
        return -1, -1


def process_amr(output):
    # arg: list of amr strings
    lines = output.split("\n", 1)
    tokens = lines[0][len("# ::tok "):].split()
    tags = nltk.pos_tag(tokens, tagset='universal')
    non_arg_span = [(i, i+1) for i, (w, t) in enumerate(tags) if t != 'NOUN']
    lines = lines[1]
    nodes = [Node(int(t[2]), int(t[3]), t[1], " ".join(tokens[int(t[2]): int(t[3])]), int(t[0])) for t in node_line.findall(lines)]
    edges = [Edge(int(t[3]), int(t[4]), t[1]) for t in edge_line.findall(lines)]
    graph = Graph(nodes, edges)
    graph.sort_node(merge_same_span=True, reverse_edge=True)
    # graph.merge_edge()
    # build a dict node_id to start_end
    span2node = {(n.start, n.end): n.id for n in graph.nodes}
    node2span = {n.id: [n.start, n.end, n.name] for n in graph.nodes}
    return graph, span2node, node2span 


def find_trigger(trigger, span2node, node2span):
    if trigger == [-1, -1]:
        return -1
    trigger_idx = trigger[1] - 1
    found = False
    for span in span2node:
        if span[0] <= trigger_idx and span[1] > trigger_idx:
            amr_idx = span2node[span]
            found = True
            break
    if not found:
        amr_idx = -1
    else:
        if not node2span[amr_idx][-1].split("-")[-1].isdigit():
            amr_idx = -1
    return amr_idx


def find_and_args(graph, node2span, and_node_id):
    and_end_spans = []
    for edge in graph.edges:
        if edge.id1 == and_node_id:
            and_end_span = node2span[edge.id2][0:2].copy()
            and_end_spans.append(and_end_span)
    return and_end_spans


def get_noun_entities(tokens, trigger_idx):
    pos_tags = nltk.pos_tag(tokens)
    pos_tag_num = len(pos_tags)
    pos_tags.append(("null", "null"))
    pos_tags[trigger_idx] = ["null", "null"]
    nouns = []

    for i in range(pos_tag_num):
        if pos_tags[i][1].startswith("NN") and (not (pos_tags[i+1][1].startswith("NN") and pos_tags[i+1][0] != '"')):
            nouns.append(i)
        elif pos_tags[i][0] == "positive" or pos_tags[i][0] == "negative":
            nouns.append(i)
        elif pos_tags[i][0][0:5].lower() == "virus":
            nouns.append(i)
        elif pos_tags[i][1].startswith("PRP"):
            nouns.append(i)

    return nouns  


def get_reachable_nodes(nodes, edges, start_id):
    child_dict = {}
    for edge in edges:
        if edge.id1 not in child_dict:
            child_dict[edge.id1] = [edge.id2]
        else:
            if edge.id2 not in child_dict[edge.id1]:
                child_dict[edge.id1].append(edge.id2)

    reachable, queue = [], []
    queue.append(start_id)
    while len(queue) != 0:
        start = queue.pop(0)
        if start not in reachable:
            reachable.append(start)
        if start in child_dict:
            for end in child_dict[start]:
                if end not in reachable:
                    queue.append(end)

    return reachable


def find_args(tokens, spans, trigger_type, trigger_idx, graph, node2span, role_map):
    node_id_to_idx = {}
    for i, node in enumerate(graph.nodes):
        node_id_to_idx[node.id] = i

    args_list = []
    if trigger_idx == -1:
        return []
    trigger_pos = graph.nodes[node_id_to_idx[trigger_idx]].start
    nouns = get_noun_entities(tokens, trigger_pos)
    
    if trigger_type.lower() not in role_map:
        return []
    mapping = role_map[trigger_type.lower()]

    already = {}
    for role_name, amr_type in mapping.items():
        if role_name != "Place":
            for edge in graph.edges:
                if edge.id1 == trigger_idx and edge.rel == amr_type:
                    next_node = edge.id2
                    reachable_nodes = get_reachable_nodes(graph.nodes, graph.edges, next_node)
                    span_candidates = []
                    for child in reachable_nodes:
                        span_candidates.append((graph.nodes[node_id_to_idx[child]].start, graph.nodes[node_id_to_idx[child]].end))
                    # check which of the entities satisfy the span candidates
                    for noun_id in nouns:
                        for span in span_candidates:
                            if span[0] <= noun_id and span[1] > noun_id:
                                if ([span[0], span[1]], role_name) not in args_list and (span[0], span[1]) not in already:
                                    args_list.append(([span[0], span[1]], role_name))
                                    already[(span[0], span[1])] = 1
        else:
            # handle place argument individually
            reachable_nodes = get_reachable_nodes(graph.nodes, graph.edges, trigger_idx)
            for edge in graph.edges:
                if edge.rel == "location" and edge.id1 in reachable_nodes:
                    start = graph.nodes[node_id_to_idx[edge.id2]].start
                    end = graph.nodes[node_id_to_idx[edge.id2]].end
                    args_list.append(([start, end], role_name))

    return args_list

def extract_args(tokens_lists, span_lists, annotations, rolemap, amrs):
    # sent_list: untokenized sentences, [sent_1, sent_2, .., sent_N]
    # annotations: list of [[[start1, end1, trigger1, trigger_text1], [start2, end2, trigger2, trigger_text2]], [start1, end1, trigger1, trigger_text1], [start2, end2, trigger2, trigger_text2]], ...]
    # sent_list = ["A fake Costco product recall notice circulated on social media purporting that Kirkland-brand bath tissue had been contaminated with COVID-19 (meaning SARS-CoV-2) due to the item being made in China."]
    # annotations = [[[115, 127, "Contaminate"]]]

    triggers_list = annotations
    total_args = []
    if amrs is not None:
        for i,tokens in enumerate(tokens_lists):
            if triggers_list[i] == []:
                total_args.append([])
                continue
            
            g_i, s2n, n2s = process_amr(amrs[i])
            args_list = []
            triggers = triggers_list[i] # [[s1, e1], [s2, e2]]
            spans = span_lists[i]
            for trigger in triggers:
                node_idx = find_trigger(trigger, s2n, n2s)
                args = find_args(tokens, spans, trigger[-1], node_idx, g_i, n2s, rolemap)
                args_list.append(args)
            total_args.append(args_list)

    return tokens_lists, triggers_list, total_args


def post_processing(recombined_args, sents, annotations):

    covid_type_dict = {
        "disaster.diseaseoutbreak.unspecified": "Disease",
        "medical.intervention.unspecified": "MedicalIssue",
        "medical.vaccinate.unspecified": "VaccineTarget",
        "medical.intervention.cure": "Affliction",
        "medical.diagnosis.unspecified": "MedicalCondition",
        "socialbehavior.clean.sanitize": "Pathogen",
        "life.illness.unspecified": "Disease",
        "life.injure.illnessdegredationsickness": "Disease",
        "life.infect.unspecified": "InfectingAgent",
        "cognitive.inspection.assesstestmeasure": "ThingAssessedFor"
    }
    vaccine_type_dict = {"medical.intervention.cure": "InstrumentTreatment"}
    gov_type_dict = {"government.agreements.unspecified": "ParticipantArg1"}
    research_type_dict = {"cognitive.research.unspecified": "Researcher"}

    covid = re.compile(r'( covid([- ]?19)? )|( virus(es)? )|( coronavirus )|( flu )')
    vaccine = re.compile(r'( vaccine(s)? )|( medicine )')
    gov = re.compile(r' government(al)? ')
    research = re.compile(r'( institute(s)? )|( (agenc)[y(ies)] )|( universit[y(ies)] )')

    for i,sent in enumerate(sents):
        triggers = annotations[i]
        args = recombined_args[i] if i < len(recombined_args) else []

        for j in range(len(triggers)):
            # j-th trigger
            trigger_j = triggers[j]
            event_type = trigger_j[-1]
            if j >= len(args):
                # did not run AMR based args
                args.append([])

            # finding covid:
            if event_type.lower() in covid_type_dict:
                span_iters = covid.finditer(sent.lower())
                for item in span_iters:
                    start, end = item.span()[0] + 1, item.span()[1] - 1
                    idx = get_span_index(args[j], start, end)
                    if ([start, end], covid_type_dict[event_type.lower()]) not in args[j]:
                        args[j].append(([start, end], covid_type_dict[event_type.lower()]))
                    if idx != -1:
                        args[j].pop(idx)
            
            # finding vaccine:
            if event_type.lower() in vaccine_type_dict:
                span_iters = vaccine.finditer(sent.lower())
                for item in span_iters:
                    start, end = item.span()[0] + 1, item.span()[1] - 1
                    idx = get_span_index(args[j], start, end)
                    if ([start, end], vaccine_type_dict[event_type.lower()]) not in args[j]:
                        args[j].append(([start, end], vaccine_type_dict[event_type.lower()]))
                    if idx != -1:
                        args[j].pop(idx)
            
            # looking for government institutes:
            if event_type.lower() in gov_type_dict:
                span_iters = gov.finditer(sent.lower())
                for item in span_iters:
                    start, end = item.span()[0] + 1, item.span()[1] - 1
                    if ([start, end], gov_type_dict[event_type.lower()]) not in args[j]:
                        args[j].append(([start, end], gov_type_dict[event_type.lower()]))
            
            # looking for research institutes:
            if event_type.lower() in research_type_dict:
                span_iters = research.finditer(sent.lower())
                for item in span_iters:
                    start, end = item.span()[0] + 1, item.span()[1] - 1
                    if ([start, end], research_type_dict[event_type.lower()]) not in args[j]:
                        args[j].append(([start, end], research_type_dict[event_type.lower()]))      

        recombined_args.append(args)     


def get_span_index(arg_spans, start, end):
    for i,item in enumerate(arg_spans):
        if item[0][0] == start and item[0][1] == end:
            return i
    return -1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_file', type=str, default="/")
    parser.add_argument('--json_output', type=str, default="/")
    parser.add_argument('--visual_output', type=str, default="/")
    parser.add_argument('--use_amr', action='store_true', help="whether to use AMR")
    args = parser.parse_args()

    data_file_name = args.data_file
    visual_res = args.visual_output
    final_res = args.json_output

    role_map_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "role_map.json")

    with open(role_map_dir, 'r', encoding="utf-8") as f:
        rolem = json.loads(f.read())

    t = TreebankWordTokenizer()

    if args.use_amr:
        amrs = amr_parse_file(data_file_name)
    else:
        amrs = None

    texts, span_lists, sent_ids, tokens, sents, offsets = [], [], [], [], [], []
    # tokenization
    with open(data_file_name, "r", encoding="utf-8") as f:
        done = 0
        while not done:
            line = f.readline()
            if line != "":
                data_d = json.loads(line)
                sent = data_d["tokens"]
                # print('sent', sent)
                spans = list(t.span_tokenize(sent)) # spans = list(t.span_tokenize(' '.join(sent)))
                span_lists.append(spans.copy())
                new_text_line = []
                for span in spans:
                    new_text_line.append(sent[span[0]: span[1]])
                texts.append(new_text_line)
            else:
                done = 1
    texts = texts
    lines = []
    with open(data_file_name, "r", encoding="utf-8") as f:
        done = 0
        while not done:
            line = f.readline()
            if line != "":
                data_d = json.loads(line)
                lines.append(data_d)
            else:
                done = 1

    # align annotations to token level
    a = [line["annotations"] for line in lines]
    triggers_list = []
    for i in range(len(texts)):
        triggers = []
        span_list, tokens_list = span_lists[i], texts[i]
        for trigger in a[i]:
            trig_s, trig_e = align(span_list, trigger)
            if trigger[-1].endswith(" "):
                triggers.append([trig_s, trig_e, trigger[-1][0:-1]].copy())
            else:
                triggers.append([trig_s, trig_e, trigger[-1]].copy())
        triggers_list.append(triggers.copy())

    s_list = [line["tokens"] for line in lines]

    ts, trigs, args = extract_args(texts, span_lists, triggers_list, rolem, amrs)
    recombined_args = []
    for i,arg in enumerate(args):
        span_list_i = span_lists[i]

        sent_event_list = []

        for trigger in arg:
            recomb_args_list = []
            for role in trigger:
                new_role_start = span_list_i[role[0][0]][0]
                new_role_end = span_list_i[role[0][1]-1][1]
                recomb_args_list.append(([new_role_start, new_role_end], role[-1]))
            sent_event_list.append(recomb_args_list)
        
        recombined_args.append(sent_event_list)

    post_processing(recombined_args, s_list, a)

    with open(visual_res, "w", encoding="utf-8") as f:
        for i in range(len(trigs)):
            trig = a[i]
            arg = recombined_args[i]
            result_dict = {"sentence": s_list[i], "events": [], "annotations": []}
            for j,trigger in enumerate(trig):
                new_event = {"trigger": s_list[i][trigger[0]: trigger[1]] + " --- " + trigger[2]}
                args_list = []
                for argument in arg[j]:
                    args_list.append(s_list[i][argument[0][0]:argument[0][1]] + " --- " + argument[1])
                new_event["arguments"] = args_list
                result_dict["events"].append(new_event)
            f.write(json.dumps(result_dict, indent=4, separators=(',',':')) + '\n')

    with open(final_res, "w", encoding="utf-8") as f:
        for i in range(len(s_list)):
            trig = a[i]
            arg = recombined_args[i]
            result_dict = {"id": i, "sentence": s_list[i], "events": []}
            for j,trigger in enumerate(trig):
                new_event = {"trigger": trigger}
                args_list = []
                for argument in arg[j]:
                    args_list.append(argument)
                new_event["arguments"] = args_list
                result_dict["events"].append(new_event)
            f.write(json.dumps(result_dict)+'\n')