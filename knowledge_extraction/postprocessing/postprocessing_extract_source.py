import re
import csv

import os
import argparse


def extract_source(url):

    if url.startswith('https://www.') or url.startswith('http://www.'):
        # url with www
        source = url.split('.')[1]
    else:
        # url without www
        pattern = re.compile(r'http[s]*://\w+\.(\w+)\.\w{3}')
        match_object = pattern.match(url)
        if match_object is None:
            if url.startswith('https://'):
                source = url[8:].split('.')[0].strip()
            elif url.startswith('http://'):
                source = url[7:].split('.')[0].strip()
            else:
                source = 'Null'
                print('cannot extract source from: ', url)
        else:
            source = match_object.group(1)
    return source

# print(extract_source('https://actualidad.rt.com/actualidad/view/140714-maduro-venezuela-guerra-biologica-epidemia'))
# print(extract_source('https://tass.ru/obschestvo/1449778'))
print(extract_source('https://www.washingtonpost.com/news/monkey-cage/wp/2017/08/01/venezuelas-dubious-new-constituent-assembly-explained/'))



# extract source from tab file:
def save_source(input_tab_file, output_tab_file):
    f = open(input_tab_file,encoding = 'utf-8',newline='')                                                                                          
    data = csv.reader(f, delimiter='\t')

    count = 0
    source_set = set()
    new_rows = []
    for row in data:
        if count == 0:
            count+=1
            row.append('source')
            new_rows.append(row)
            
            continue
        parent_uid = row[2]
        children_uid = row[3]
        key = parent_uid+'_'+children_uid

        url = row[4]
        extracted_source = extract_source(url)

        row.append(extracted_source)
        new_rows.append(row)

    f.close()

    with open(output_tab_file, 'w', encoding = 'utf-8',newline='') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        for r in new_rows:
            tsv_writer.writerow(r)

    print('output to file: ', output_tab_file)


# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description='Extract source from URL in tab file')
#     parser.add_argument('-i', '--input_tab_file_path', help='Input file path', required=True)
#     parser.add_argument('-o', '--output_tab_file_path', help='Output file path', required=True)
#     args = vars(parser.parse_args())

#     input_tab_file = args['input_tab_file_path']
#     output_tab_file = args['output_tab_file_path']
#     save_source(input_tab_file, output_tab_file)