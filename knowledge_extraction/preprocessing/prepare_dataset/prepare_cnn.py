import subprocess
import os
import json
import shutil
from sys import meta_path
# from PIL import Image

cnn_dir = '/shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/rawdata/cnn_ukraine_newstext'
output_dir = '/shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/en'
output_dir_rsd = os.path.join(output_dir, 'rsd')
meta_path = '/shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/rawdata/meta_data.json'

os.makedirs(output_dir_rsd, exist_ok=True)

meta_data = json.load(open(meta_path))

dict_url = dict()
for date_dir in os.listdir(cnn_dir):
    if os.path.isdir(os.path.join(cnn_dir, date_dir)):
        date_str = "2022-"+date_dir[:5]
        for txtfile in os.listdir(os.path.join(cnn_dir, date_dir)):
            filename = date_str+'_'+txtfile.replace('.txt', '.rsd.txt')
            content = open(os.path.join(cnn_dir, date_dir, txtfile), 'r').read()
            with open(os.path.join(output_dir_rsd, filename), 'w') as writer:
                writer.write(content)
            if txtfile.replace('.txt', '') in meta_data:
                url = meta_data[txtfile.replace('.txt', '')]['url']
                dict_url[date_str+'_'+txtfile.replace('.txt', '')] = url

json.dump(dict_url, open(os.path.join(output_dir, 'url.json'), 'w'), indent=4)

# python /shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/knowledge_extraction/preprocessing/rsd2ltf.py --seg_option nltk+linebreak --tok_option nltk_wordpunct --extension .rsd.txt ${rsd_dir} ${ltf_dir}

# write parent_child.tab
with open(os.path.join((output_dir), 'parent_children.tab'), 'w') as writer_parent_child:
    # catalog_id	version	parent_uid	child_uid	url	child_asset_type	topic	lang_id	lang_manual	rel_pos	wrapped_md5	unwrapped_md5	download_date	content_date	status_in_corpus
    writer_parent_child.write('catalog_id	version	parent_uid	child_uid	url	child_asset_type	topic	lang_id	lang_manual	rel_pos	wrapped_md5	unwrapped_md5	download_date	content_date	status_in_corpus')
    for txt_file in os.listdir(output_dir_rsd):
        if txt_file.endswith('.rsd.txt'):
            docid = txt_file.replace('.rsd.txt', '')        
            date_str = txt_file[:10]
            writer_parent_child.write('0\t0\t%s\t%s\t%s\t0\t0\t0\t0\t0\t0\t0\t0\t0\t%s\t0\n' % (
                docid, docid, url, date_str
            ))

