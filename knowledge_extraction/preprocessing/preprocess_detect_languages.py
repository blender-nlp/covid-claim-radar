from langdetect import detect, DetectorFactory
import shutil
import os
import argparse
import io
import xml.etree.ElementTree as ET

def get_column_idx(parent_child_file):
    try:
        for line in open(parent_child_file):
            line = line.rstrip('\n')
            tabs = line.split('\t')
            # print(tabs)
            child_id_column = tabs.index("child_uid")
            lang_id_column = tabs.index("lang_id")
            return child_id_column, lang_id_column
    except:
        print('[ERROR] parent child file do not have child_uid, parent_uid, content_date')
        child_id_column = 3
        lang_id_column = 7 
        return child_id_column, lang_id_column


def get_lang_metadata(parent_child_tab_path):
    child_column_idx, lang_column_idx = get_column_idx(parent_child_tab_path)
    lang_id_mapping = {'spa':'es', 'eng':'en', 'rus':'ru', 'ukr':'uk'}

    docid_to_lang = dict()

    f = open(parent_child_tab_path)
    f.readline()

    for one_line in f:
        one_line = one_line.strip()
        one_line_list = one_line.split('\t')
        doc_id = one_line_list[child_column_idx]
        lang_id = one_line_list[lang_column_idx]
        if lang_id.lower() != 'n/a' and len(lang_id) == 3:
            if lang_id in lang_id_mapping:
                docid_to_lang = lang_id_mapping[lang_id]
    return docid_to_lang


# def get_lang_ltf(ltf_file_path):
#     tree = ET.parse(ltf_file_path)
#     root = tree.getroot()
#     for doc in root:
#         for text in doc:
            


def detect_lang(rsd_input_folder, ltf_input_folder, output_folder, langs=['en', 'ru', 'uk'], parent_child_tab_path=None):

    try:
        if parent_child_tab_path is not None:
            docid_to_lang = get_lang_metadata(parent_child_tab_path)
    except:
        docid_to_lang = {}

    DetectorFactory.seed = 0

    # if os.path.exists(output_folder) is True:
    #     shutil.rmtree(output_folder)
    #
    # os.mkdir(output_folder)

    # rsd_input_folder = os.path.join(input_folder, 'rsd')
    # ltf_input_folder = os.path.join(input_folder, 'ltf')
    for one_file in os.listdir(rsd_input_folder):
        if not one_file.endswith('.rsd.txt'):
            continue
        one_file_id = one_file.replace('.rsd.txt', '')
        one_rsd_file_path = os.path.join(rsd_input_folder, one_file)
        one_ltf_file_path = os.path.join(ltf_input_folder, '%s.ltf.xml' % one_file_id)
        one_file_content = io.open(one_rsd_file_path, mode='r', encoding='utf-8').read()
        try:
            candidate_language_id = detect(one_file_content)
        except:
            # if one_file in docid_to_lang:
            #     candidate_language_id = docid_to_lang[one_file]
            # else:
            #     candidate_language_id = 'en'
            candidate_language_id = 'en'
        candidate_language_id = candidate_language_id.replace('zh-cn', 'zh')
        if candidate_language_id not in langs:
            candidate_language_id = 'en'

        if candidate_language_id == 'en':
            language_folder_ltf = os.path.join(output_folder, candidate_language_id, 'ltf')
        else:
            language_folder_ltf = os.path.join(output_folder, candidate_language_id, 'ltf_raw')
        if os.path.exists(language_folder_ltf) is False:
            os.makedirs(language_folder_ltf, exist_ok=True)
        shutil.copy(one_ltf_file_path, language_folder_ltf)
        
        if candidate_language_id == 'en':
            language_folder_rsd = os.path.join(output_folder, candidate_language_id, 'rsd')
        else:
            language_folder_rsd = os.path.join(output_folder, candidate_language_id, 'rsd_raw')
        if os.path.exists(language_folder_rsd) is False:
            os.makedirs(language_folder_rsd, exist_ok=True)
        shutil.copy(one_rsd_file_path, language_folder_rsd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('rsd_input_folder', type=str,
                        help='input directory of all rsd files')
    parser.add_argument('ltf_input_folder', type=str,
                        help='input directory of all ltf files')
    parser.add_argument('output_folder', type=str,
                        help='output directory divided by languages')
    parser.add_argument('--langs', default=['en', 'ru', 'uk'], nargs='+', type=str,
                        help='langs')
    parser.add_argument('--parent_child_tab_path', default=None, type=str,
                        help='parent_children.tab')
    args = parser.parse_args()

    rsd_input_folder = args.rsd_input_folder
    ltf_input_folder = args.ltf_input_folder
    output_folder = args.output_folder
    parent_child_tab_path = args.parent_child_tab_path
    langs = args.langs
    # input_folder = '/data/m1/AIDA_Data/LDC_raw_data/LDC2018E01_AIDA_Seedling_Corpus_V2.0/data/'
    # output_folder = '/data/m1/zhangt13/aida2018/1118/E01/source'

    # input_folder = '/data/m1/lim22/aida2019/dryrun_3/dryrun/data'
    # output_folder = '/data/m1/lim22/aida2019/dryrun_3/source'
    # input_folder = '/data/m1/AIDA_Data/LDC_raw_data/LDC2019E42_AIDA_Phase_1_Evaluation_Source_Data_V1.0/data'
    # rsd_input_folder = os.path.join(input_folder, 'rsd')
    # ltf_input_folder = os.path.join(input_folder, 'ltf','ltf')
    # output_folder = '/data/m1/lim22/aida2019/LDC2019E42/source'

    detect_lang(rsd_input_folder, ltf_input_folder, output_folder, langs, parent_child_tab_path)
