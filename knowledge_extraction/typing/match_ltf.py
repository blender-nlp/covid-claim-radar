import os
import xml.etree.ElementTree as ET
import argparse

def parse_offset_str(offset_str):
    doc_id = offset_str[:offset_str.rfind(':')]
    start = int(offset_str[offset_str.rfind(':') + 1:offset_str.rfind('-')])
    end = int(offset_str[offset_str.rfind('-') + 1:])
    return doc_id, start, end

def revise_offset_match_ltf(doc_id, start, end, mention_str, tf_dir):
    # tokens = []
    new_start = -1
    new_end = -1

    ltf_file_path = os.path.join(ltf_dir, doc_id + '.ltf.xml')
    if not os.path.exists(ltf_file_path):
        return '[ERROR]NoLTF %s' % doc_id
    tree = ET.parse(ltf_file_path)
    root = tree.getroot()
    # tokens = list()
    for doc in root:
        for text in doc:
            for seg in text:
                for token in seg:
                    if token.tag == "TOKEN":
                        
                        token_beg = int(token.attrib["start_char"])
                        token_end = int(token.attrib["end_char"])
                        
                        # if the offset is located in the middle of a word
                        if start >= token_beg and start <= token_end:
                            # print(token_beg, token_end, token.text)
                            new_start = token_beg
                        if end >= token_beg and end <= token_end:
                            # print(token_beg, token_end)
                            new_end = token_end
    if new_start == -1 or new_end == -1:
        doc_id, new_start, new_end = revise_offset_match_ltf_string(doc_id, start, end, mention_str, ltf_dir)
    # if new_end - new_start != end - start:
    #     return None, None, None

    return doc_id, new_start, new_end #, ' '.join(tokens)

def revise_offset_match_ltf_string(doc_id, start, end, mention_str, ltf_dir):
    # tokens = []
    new_start = -1
    new_end = -1

    ltf_file_path = os.path.join(ltf_dir, doc_id + '.ltf.xml')
    if not os.path.exists(ltf_file_path):
        return '[ERROR]NoLTF %s' % doc_id
    tree = ET.parse(ltf_file_path)
    root = tree.getroot()
    # tokens = list()
    for doc in root:
        for text in doc:
            for seg in text:
                seg_beg = int(seg.attrib["start_char"])
                seg_end = int(seg.attrib["end_char"])
                if start >= seg_beg-10 and end <= seg_end+10:
                    for token in seg:
                        if token.tag == "TOKEN":
                            token_beg = int(token.attrib["start_char"])
                            token_end = int(token.attrib["end_char"])
                            if mention_str == token.text:
                                new_start = token_beg
                                new_end = token_end
                                break

    return doc_id, new_start, new_end


def revise_offset_match_ltf_stringsearch(doc_id, start, end, mention_str, ltf_dir):
    # tokens = []
    new_start = -1
    new_end = -1
    new_end_ = -1
    new_start_ = -1

    ltf_file_path = os.path.join(ltf_dir, doc_id + '.ltf.xml')
    if not os.path.exists(ltf_file_path):
        return '[ERROR]NoLTF %s' % doc_id
    tree = ET.parse(ltf_file_path)
    root = tree.getroot()
    # tokens = list()
    for doc in root:
        for text in doc:
            for seg in text:
                seg_beg = int(seg.attrib["start_char"])
                seg_end = int(seg.attrib["end_char"])
                # 
                if start >= seg_beg-10 and end <= seg_end+10:
                    # print(seg_beg, seg_end, start, end)
                    for token in seg:
                        if token.tag == "ORIGINAL_TEXT":
                            if mention_str in token.text:
                                new_start_ = token.text.find(mention_str) + seg_beg
                                new_end_ = new_start_ + len(mention_str) - 1
                                # print("new", new_start_, new_end_)
                    if new_start_ != -1 and new_end_ != -1:
                        for token in seg:
                            if token.tag == "TOKEN":
                                token_beg = int(token.attrib["start_char"])
                                token_end = int(token.attrib["end_char"])
                                # if the offset is located in the middle of a word
                                if new_start_ >= token_beg and new_start_ <= token_end:
                                    new_start = token_beg
                                if new_end_ >= token_beg and new_end_ <= token_end:
                                    new_end = token_end

    return doc_id, new_start, new_end


def get_str_from_rsd(doc_id, start, end, rsd_dir):
    rsd_file_path = os.path.join(rsd_dir, doc_id + '.rsd.txt')
    if os.path.exists(rsd_file_path):
        rsd_content = open(rsd_file_path).read()
        return rsd_content[start:end+1].replace('\n',' ')

def load_cs(input_cs, output_cs, ltf_dir, rsd_dir):
    removed = set()
    new_lines = []
    with  open(output_cs, 'w') as writer:
        for line in open(input_cs):
            line = line.rstrip('\n')
            tabs = line.split('\t')

            if line.startswith(':Entity'):
                if 'Filler' in tabs[0]: #or 'FINE' in tabs[0] or 'ARG' in tabs[0]:
                    if 'mention' in tabs[1] and tabs[1] != 'normalized_mention':
                        offset = tabs[3]
                        mention_str = tabs[2][1:-1]
                        doc_id, start, end = parse_offset_str(offset)
                        doc_id, new_start, new_end = revise_offset_match_ltf(doc_id, start, end, mention_str, ltf_dir)
                        if (new_start == -1) or (new_end == -1):
                            doc_id, new_start, new_end = revise_offset_match_ltf_stringsearch(doc_id, start, end, mention_str, ltf_dir)
                        if (new_start == -1) or (new_end == -1) or (new_end-new_start > 100):
                            print('removed', new_start, new_end, new_end-new_start, line)
                            removed.add(tabs[0])
                            continue
                        if new_start != start or new_end != end:
                            # print(tabs[0])
                            tabs[3] = '%s:%d-%d' % (doc_id, new_start, new_end)
                            tabs[2] = '"%s"' % get_str_from_rsd(doc_id, new_start, new_end, rsd_dir)
                            new_lines.append('\t'.join(tabs))
                            # writer.write('\n')
                        else:
                            new_lines.append(line.replace('0.00', '1.00'))
                            # writer.write('\n')
                    else:
                        new_lines.append(line.replace('0.00', '1.00'))
                        # writer.write('\n')
                else:
                    new_lines.append(line.replace('0.00', '1.00'))
                    # writer.write('\n')              
            else:
                new_lines.append(line.replace('0.00', '1.00'))
                # writer.write('\n')

        for line in new_lines:
            id = line.split('\t')[0]
            if id in removed:
                continue
            writer.write(line)
            writer.write('\n')
        writer.flush()
        writer.close()
                
    print('finished revising cs')     
    # writer.flush()
    # writer.close()

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rsd_dir', type=str,
                        help='input rsd file path or directory.')
    parser.add_argument('--ltf_dir', type=str,
                        help='output ltf file path or directory.')
    parser.add_argument('--input_cs', type=str,
                        help='input rsd file path or directory.')
    parser.add_argument('--output_cs', type=str,
                        help='output ltf file path or directory.')
    args = parser.parse_args()

    rsd_dir = args.rsd_dir
    ltf_dir = args.ltf_dir
    input_cs = args.input_cs
    output_cs = args.output_cs

    load_cs(input_cs, output_cs, ltf_dir, rsd_dir)