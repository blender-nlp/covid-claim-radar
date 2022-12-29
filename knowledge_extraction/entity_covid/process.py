import os
import json
from xml.dom.minidom import parse
import re

# #util
# intersect, exactly, elem
def e_intersect(elem,lis):
    file_name, offsets = elem.split(':')
    st,ed = offsets.split('-')
    st,ed = int(st),int(ed)
    for e in lis:
        e_file_name, e_offsets = e.split(':')
        e_st,e_ed = e_offsets.split('-')
        e_st,e_ed = int(e_st),int(e_ed)
        if e_file_name==file_name:
            if st<=e_ed and ed>=e_st:
                if st==e_st and ed==e_ed:
                    return True, True, e
                else:
                    return True, False, e
    return False, False, None

def intersect(lis1,lis2):
    for e in lis1:
        if e in lis2:
            return True
    return False


# import inflect
# in_eng = inflect.engine()

import argparse
parser = argparse.ArgumentParser(description='Choose Language')
parser.add_argument('--ltf', type=str,
                    help='ltf folder')
parser.add_argument('--entity', type=str,
                    help='entity file')
parser.add_argument('--out', type=str,
                    help='output dir')
args = parser.parse_args()
# ---------Match------------
# entity_file = 'aida_hackathon_merged/entity.cs'
# ltf_folder = 'ltf'

# entity_file = 'merged_fine_all_{}.cs'.format(args.lan)
entity_file = args.entity
ltf_folder = args.ltf

eng_keywords_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keywords.json')
eng_qnode_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qnode_map.json')


if not os.path.exists(args.out):
    os.makedirs(args.out)

out_file = args.out+'/entity.cs'

# Find already detected entity
dic = {}
ent2keyline = {}
tmp = []
with open(entity_file,'r') as f:
    # line1 = f.readline().strip()
    # line2 = f.readline().strip()
    # line = f.readline().strip()
    # while line:
    for line in f.readlines():
        line = line.strip()
        last_line = line
        if line.split('\t')[1]=='type':
            dic[line] = [line]
            key_line = line
            tmp.append(line.split('\t')[2].split('#')[-1])
        else:
            dic[key_line].append(line)
            if line.split('\t')[1]!='link':
                ent2keyline[line.split('\t')[3]] = key_line
        line = f.readline().strip()

last_num = int(last_line.split('\t')[0].split('_')[-1])

# load keywords dict
dict_keywords2type = {}
for lan,keywords_file in [('eng',eng_keywords_file)]:
    with open(keywords_file,'r') as f:
        type2keywords = json.load(f)

    _keywords2type = {}
    for key,vals in type2keywords.items():
        for val in vals:
            _keywords2type[val.lower()]=key

    _keywords2type = sorted(list(_keywords2type.items()), key= lambda x:len(x[0].split(' ')), reverse=True)
    _keywords2type = dict(_keywords2type)
    dict_keywords2type[lan] = _keywords2type

#load qnode map
dict_word2qnode = {}
for lan,qnode_file in [('eng',eng_qnode_file)]:
    with open(qnode_file,'r') as f:
        _word2qnode = json.load(f)
    __word2qnode = {}
    for k,v in _word2qnode.items():
        __word2qnode[k.lower()] = v
    dict_word2qnode[lan] = __word2qnode

# all ents
all_ents = list(set(list(ent2keyline.keys())))

# match keyword
ltf_files = [e for e in os.listdir(ltf_folder) if e.endswith('.ltf.xml')]
from tqdm import tqdm
for ltf_file in tqdm(ltf_files):
    DOMtree = parse(ltf_folder+'/'+ltf_file)
    collection = DOMtree.documentElement
    seg_nodes = collection.getElementsByTagName("SEG")
    lan = collection.getElementsByTagName("DOC")[0].getAttribute("lang")
    lan= 'eng'
    if lan=='eng':
        keywords2type = dict_keywords2type[lan]
        word2qnode = dict_word2qnode[lan]
    else:
        continue
    for seg_node in seg_nodes:
        # seg_st = int(seg_node.getAttribute("start_char"))
        # seg_ed = int(seg_node.getAttribute("end_char"))
        # text = str(seg_node.getElementsByTagName("ORIGINAL_TEXT")[0].childNodes[0].data)
        # for keyword, ent_type in keywords2type.items():
        #     offsets = [substr.start() for substr in re.finditer(keyword.lower() , text.lower())]
        #     for offset in offsets:
        #         ent_st = seg_st + offset
        #         ent_ed = seg_st + len(keyword)-1
        #         ent_tag = ltf_file[:-8]+':{}-{}'.format(ent_st,ent_ed)
        #         if intersect(ent_tag,all_ents):
        #             continue
        #         ent_str = text[offset:offset+len(keyword)]
        #         last_num = last_num+1
        #         ent_head = ':Entity_EDL_'+ '%07d' % last_num 
        #         ent_type_line = ent_head +'\ttype\t{}'.format(ent_type)
        #         ent_mention_line1 = ent_head+"\tcanonical_mention\t\"{}\"\t{}\t1.0".format(ent_str,ent_tag)
        #         ent_mention_line2 = ent_head+"\tnominal_mention\t\"{}\"\t{}\t1.0".format(ent_str,ent_tag)
        #         ent_link_line = ent_head+"\tlink\tQ0\t0.8"
        #         dic[ent_type_line] = []
        #         dic[ent_type_line].append(ent_mention_line1)
        #         dic[ent_type_line].append(ent_mention_line2)
        #         dic[ent_type_line].append(ent_link_line)
        #         print(ent_str)
        #         print(ent_type)
        
        token_nodes = seg_node.getElementsByTagName("TOKEN")
        token_node_id = 0
        while token_node_id < len(token_nodes):
            # token_node = token_nodes[token_node_id]
            # ent_st = token_node.getAttribute("start_char")
            # ent_ed = token_node.getAttribute("end_char")
            # ent_tag = ltf_file[:-8]+':{}-{}'.format(ent_st,ent_ed)
            # ent_str = str(token_node.childNodes[0].data)
            for keyword, ent_type in keywords2type.items():
                keyword_len = len(keyword.split(' '))
                if token_node_id + keyword_len<=len(token_nodes): 
                    ent_st = token_nodes[token_node_id].getAttribute("start_char")
                    ent_ed = token_nodes[token_node_id+ keyword_len-1].getAttribute("end_char")
                    ent_tag = ltf_file[:-8]+':{}-{}'.format(ent_st,ent_ed)
                    ent_str = ' '.join([str(token_node.childNodes[0].data) for token_node in token_nodes[token_node_id:token_node_id+ keyword_len]])
                    # try:
                    # ent_str2_tmp = [in_eng.singular_noun(str(token_node.childNodes[0].data)) for token_node in token_nodes[token_node_id:token_node_id+ keyword_len]]
                    # ent_str2 = []
                    # for kkk in ent_str2_tmp:
                    #     if kkk!=False:
                    #         ent_str2.append(kkk)
                    #     else:
                    #         ent_str2.append('EMPTY')
                    # ent_str2 = ' '.join(ent_str2)
                    # except:
                    # print(ent_str1)
                    # print(ent_str2)
                    # for token_node in token_nodes[token_node_id:token_node_id+ keyword_len]:
                    #     print(in_eng.singular_noun(str(token_node.childNodes[0].data)))
                    # exit(100)
                    if keyword.lower()==ent_str.lower():
                        # if keyword.lower() == ent_str1.lower():
                        #     ent_str = ent_str1
                        # else:
                        #     ent_str = ent_str2
                        a,isExact,b =  e_intersect(ent_tag,all_ents)
                        if a:
                            if isExact:
                                b_line = ent2keyline[b]
                                # print("dic[b_line][0].split('#')[0]", dic[b_line][0].split('#')[0])
                                dic[b_line][0] = dic[b_line][0].split('#')[0].split('\t')[0] +'\ttype\t' + ent_type+'\t1.000000' #dic[b_line][0].split('#')[0]+'#'+ent_type+'\t1.000000'
                            # print('change:',b,'---->',ent_type)
                            continue
                        last_num = last_num+1
                        ent_type = keywords2type[ent_str.lower()]
                        ent_head = ':Entity_EDL_'+ '%07d' % last_num 
                        ent_type_line = ent_head +'\ttype\t{}\t1.000000'.format(ent_type)
                        # ent_mention_line1 = ent_head+"\tcanonical_mention\t\"{}\"\t{}\t1.0".format(ent_str,ent_tag)
                        ent_mention_line2 = ent_head+"\tnominal_mention\t\"{}\"\t{}\t1.0".format(ent_str,ent_tag)
                        # print(ent_str)
                        # print(ent_type)
                        # print(ent_tag)
                        qn = 'Q0' if ent_str.lower() not in word2qnode else word2qnode[ent_str.lower()]
                        ent_link_line = ent_head+"\tlink\t{}\t0.8".format(qn)
                        dic[ent_type_line] = [ent_type_line]
                        # dic[ent_type_line].append(ent_mention_line1)
                        dic[ent_type_line].append(ent_mention_line2)
                        dic[ent_type_line].append(ent_link_line)
                        token_node_id = token_node_id+ keyword_len -1 
                        break
            token_node_id = token_node_id+1


with open(out_file+"_bak",'w') as f:
    # f.write(line1+'\n')
    # f.write(line2+'\n')
    for key,vals in dic.items():
        for val in vals:
            f.write(val+'\n')



# post-process
print('---post processing---')
path = out_file

dic = {}
ent2keyline = {}
with open(out_file+"_bak",'r') as f:
    # line1 = f.readline().strip()
    # line2 = f.readline().strip()
    # line = f.readline().strip()
    # while line:
    for line in f.readlines():
        line = line.strip()
        if line.split('\t')[1]=='type':
            # print('line', line)
            line = line.replace(' ','\t')
            if len(line.split('\t'))!=4:
                print('line', line)
                assert len(line.split('\t'))==3
                line = line+'\t1.000000'
            
            entId = line.split('\t')[0]
            if entId in ent2keyline:
                lineScore = float(line.split('\t')[-1])
                # print(lineScore)
                previousScore = float(ent2keyline[entId].split('\t')[-1])
                if lineScore>=previousScore:
                    dic[ent2keyline[entId]] = []
                    ent2keyline[entId] = line
                else:
                    line = f.readline().strip()
                    continue
            else:
                ent2keyline[entId] = line

            dic[line] = [line]
            key_line = line
        else:
            dic[key_line].append(line)
        line = f.readline().strip()

with open(path,'w') as f:
    # f.write(line1+'\n')
    # f.write(line2+'\n')
    for key,vals in dic.items():
        for val in vals:
            f.write(val+'\n')