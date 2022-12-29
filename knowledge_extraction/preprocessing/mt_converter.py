import xml.etree.ElementTree as ET
import os
from collections import defaultdict
import json
import argparse
import shutil

def get_rsd_sent_mapping(ltf_file_path_isi, rsd_file_path_trans):
    sent_mapping_raw2trans = defaultdict(lambda : defaultdict())
    sent_mapping_trans2raw = defaultdict(lambda : defaultdict())
    seg_end_trans = 0 # ending char is starting from 0
    rsd_content = ""

    if not os.path.exists(ltf_file_path_isi):
        print('[ERROR]NoLTF %s' % ltf_file_path_isi)
        return '[ERROR]NoLTF %s' % ltf_file_path_isi
    writer = open(rsd_file_path_trans, 'w')

    tree = ET.parse(ltf_file_path_isi)
    root = tree.getroot()
    for doc in root:
        for text in doc:
            for seg in text:
                seg_beg = int(seg.attrib["start_char"])
                seg_end = int(seg.attrib["end_char"])
                for token in seg:
                    if token.tag == "TRANSLATED_TEXT":
                        seg_beg_trans = seg_end_trans
                        if len(rsd_content) > 1:
                            # it is the second sentence, add one space before appending
                            rsd_content += '\n'
                            seg_end_trans += 1
                            seg_beg_trans += 1
                        rsd_content += token.text if token.text is not None else ""
                        seg_end_trans += len(token.text) 
                        sent_mapping_raw2trans[seg_beg][seg_end] = (seg_beg_trans, seg_end_trans-1)
                        sent_mapping_trans2raw[seg_beg_trans][seg_end_trans-1] = (seg_beg, seg_end)
                    if token.tag == 'DETECTED_LANGUAGE':
                        language = token.text

    writer.write(rsd_content)
    writer.flush()
    writer.close()

    return sent_mapping_raw2trans, sent_mapping_trans2raw, language
                


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang_target', type=str,
                        help='lang_target')
    parser.add_argument('--ltf_dir_raw', type=str,
                        help='input raw ltf file path or directory.')
    parser.add_argument('--ltf_dir_trans_isi', type=str,
                        help='input translated ltf file path or directory.')
    # parser.add_argument('--ltf_dir_trans_en', type=str,
    #                     help='output ltf file path of english content.')
    parser.add_argument('--rsd_dir_trans_en', type=str,
                        help='output rsd file path of english content.')
    parser.add_argument('--mapping_dir', type=str,
                        help='output translation offset mapping_dir.')
    args = parser.parse_args()

    lang_target = args.lang_target
    ltf_dir_raw = args.ltf_dir_raw
    ltf_dir_trans_isi = args.ltf_dir_trans_isi
    # ltf_dir_trans_en = args.ltf_dir_trans_en
    rsd_dir_trans_en = args.rsd_dir_trans_en
    mapping_dir = args.mapping_dir
    # mapping_dir = '/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/LDC2022R02/%s/' % lang_target
    
    os.makedirs(rsd_dir_trans_en, exist_ok=True)
    # os.makedirs(ltf_dir_trans_en, exist_ok=True)

    docsent_mapping_raw2trans = dict()
    docsent_mapping_trans2raw = dict()
    for docfile in os.listdir(ltf_dir_raw): #os.listdir(ltf_dir_raw2): #
        # if os.path.exists(os.path.join(ltf_dir_trans_en, docfile)):
        #     continue
        docid = docfile.replace('.ltf.xml', '')
        try:
            ltf_file_path_raw = os.path.join(ltf_dir_trans_isi, 'MT-' + docid + '.ltf.xml')
            rsd_file_path_trans = os.path.join(rsd_dir_trans_en, docid + '.rsd.txt')

            sent_mapping_raw2trans, sent_mapping_trans2raw, language = get_rsd_sent_mapping(ltf_file_path_raw, rsd_file_path_trans)

            docsent_mapping_raw2trans[docid] = sent_mapping_raw2trans
            docsent_mapping_trans2raw[docid] = sent_mapping_trans2raw
        except:
            print('[MISSING] missing %s ' % docid)

    json.dump(docsent_mapping_raw2trans, open(os.path.join(mapping_dir, 'sentchar_raw2trans_%s.json') % lang_target, 'w'))
    json.dump(docsent_mapping_trans2raw, open(os.path.join(mapping_dir, 'sentchar_trans2raw_%s.json') % lang_target, 'w'))

    # python /shared/nas/data/m1/manling2/aida_docker/docker_m18/aida_utilities/rsd2ltf.py --seg_option nltk+linebreak --tok_option nltk_wordpunct --extension .rsd.txt rsd ltf