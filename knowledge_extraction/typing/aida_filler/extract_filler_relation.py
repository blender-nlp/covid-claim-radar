import os
import json
import xml.etree.ElementTree as ET
import argparse
import glob
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

def read_ltf(ltf_dir):
    ltf_dict = {}

    # for doc in glob.glob(os.path.join(ltf_dir, '*.ltf.xml')):
    for doc in os.listdir(ltf_dir):
        if not doc.endswith('.ltf.xml'):
            continue
        doc_id = doc.replace('.ltf.xml', '')
    
        
        if doc_id not in ltf_dict:
            ltf_dict[doc_id] = []
        with open(os.path.join(ltf_dir, doc)) as f:
            article = f.read()

        root = ET.fromstring(article)
        for seg in root[0][0].findall('SEG'):
            ltf_dict[doc_id].append([seg.attrib['start_char'], seg.attrib['end_char']])
#            print(ltf_dict[doc_id])
    return ltf_dict


def load_unit_gaz(units_path):
    gaz = set()
    with open(units_path) as f:
        lines = f.readlines()

    for line in lines:
        gaz.add(line.strip())
    return gaz

def single_generate(corenlp_dir, output_dir):
    ner_cache = set()
    for doc in os.listdir(corenlp_dir):
        # if not doc.endswith('.rsd.txt.json'):
        #     continue
        index = 0
        f_out = open(os.path.join(output_dir, doc.replace('.rsd.txt.json','.cs')), 'w')
        with open(os.path.join(corenlp_dir,doc)) as f:
            content = f.read()
        json_f = json.loads(content)
        for sentence in json_f['sentences']:
            for entitymention in sentence['entitymentions']:
                ner = entitymention['ner']
                if ner not in ner_cache:
                    ner_cache.add(ner)
                characterOffsetBegin = str(entitymention['characterOffsetBegin'])
                characterOffsetEnd = str(entitymention['characterOffsetEnd']-1)
                text = entitymention['text']
                if ner != 'TIME' and ner != 'DATE':
                    continue
                if ner == 'DATE':

                    print(text, characterOffsetBegin, characterOffsetEnd)
                filler_id = ':Filler_ENG_%s'%(format(index, '07d'))
                filler_type = 'TME'
                filler_offset = doc_id+':'+'-'.join([characterOffsetBegin,characterOffsetEnd])
                confidence = 1.000
                f_out.write('%s\ttype\tTME\n'%filler_id)
                f_out.write('%s\t%s\t%s\t%s\t%s\n'%(filler_id, 'mention','"'+text+'"', filler_offset, confidence))
                index += 1
        f_out.close()



def whole_generate(corenlp_dir, text_dir, unit_gaz, edl_dict, ltf_dict, lang):
    filter_token_list = ['/','\\',':','{','}','[',']']
    filler_dict = {}
    ner_cache = set()
    token_dict = {}
    text_dict = {}
    filler_index = 0
    relation_dict = {}
    edl_filter_dict = {}
    for idix,doc in enumerate(os.listdir(corenlp_dir)):
        # print('corenlp_dir',idix,doc)
        article = ''
        doc_id = doc.replace('.rsd.txt', '').replace('.json', '')
        if doc_id in edl_dict:
            edl_list = edl_dict[doc_id]
        else:
            edl_list = {}
        relation_dict[doc_id] = []
        edl_filter_dict[doc_id] = []
        ltf_sent_off = ltf_dict[doc_id]
        text_path = os.path.join(text_dir, doc_id + '.rsd.txt')
        with open(text_path) as f:
            article = f.read()
        text_dict[doc_id] = article

        with open(os.path.join(corenlp_dir,doc)) as f:
            content = f.read()
        if doc_id not in filler_dict:

            filler_dict[doc_id] = {}
            filler_dict[doc_id]['URL'] = []
            filler_dict[doc_id]['TME'] = []
            filler_dict[doc_id]['MON'] = []
            filler_dict[doc_id]['TTL'] = []
            filler_dict[doc_id]['VAL'] = []
        json_f = json.loads(content)
        
        for sentence in json_f['sentences']:
            token_list = []
            # dependency_dict = {}
            # for dependency in sentence['basicDependencies']:
            #     try:

            #         governor = dependency['governor']
            #         governorGloss = dependency['governorGloss']
            #         dependent = dependency['dependent']
            #         dependentGloss = dependency['dependentGloss']
            #         dep = dependency['dep']
                
            #         if dependent not in dependency_dict:
            #             dependency_dict[dependent] = [governor, governorGloss, dependent, dependentGloss, dep]
                        
            #         else:
            #             print('error')
            #     except:
            #         print(doc, dependency)
            for token in sentence['tokens']:
                token_list.append([token['originalText'], token['characterOffsetBegin'], token['characterOffsetEnd'], token['ner']])

            token_text_list = [x[0] for x in token_list]

            sentence_start = int(token_list[0][1])
            sentence_end = int(token_list[0][2])-1
            #provenance = doc+':'+str(sentence_start) + '-'+str(sentence_end)
            provenance = doc_id+':'+str(token_list[0][1])+'-'+str(token_list[-1][2]-1)
            for entitymention in sentence['entitymentions']:
                ner = entitymention['ner']
                if ner not in ner_cache:
                    ner_cache.add(ner)
                characterOffsetBegin = str(entitymention['characterOffsetBegin'])
                flag_xxx = None

                for i_sent,sent_x in enumerate(ltf_sent_off):
                    if int(sent_x[0]) <= int(characterOffsetBegin)  <= int(sent_x[1]):
                        x_index = i_sent
                        flag_xxx = 1
                        provenance = doc_id+':'+str(int(sent_x[0]))+'-'+str(int(sent_x[1]))
                        break
                if flag_xxx is None:
                    print('error xxxxxx', doc, characterOffsetBegin, entitymention['text'])
                characterOffsetEnd = str(entitymention['characterOffsetEnd']-1)
                index_start = entitymention['tokenBegin']
                index_end = entitymention['tokenEnd']
                text = entitymention['text']

                #if ner != 'TIME' and ner != 'DATE':
                #    continue
                if ner == 'DATE':
                    try:
                        norm_text = entitymention['normalizedNER']
                    except:
                        norm_text = text
                    filler_dict[doc_id]['TME'].append([[text,norm_text], characterOffsetBegin, characterOffsetEnd, format(filler_index, '07d')])
                    filler_index += 1
                elif ner == 'TIME':
                    try:
                        norm_text = entitymention['normalizedNER']
                    except:
                        norm_text = text

                    filler_dict[doc_id]['TME'].append([[text,norm_text], characterOffsetBegin, characterOffsetEnd, format(filler_index, '07d')])
                    filler_index += 1
                    
                #elif ner == 'DURATION':
                #    if index_end <len(token_list):
                #        print([text+' '+token_list[index_end][0], characterOffsetBegin, token_list[index_end][2]],doc)
                elif ner == 'URL':
                    filler_dict[doc_id]['URL'].append([text, characterOffsetBegin, characterOffsetEnd, format(filler_index, '07d')])
                    filler_id = ':Filler_%s_%s'%(lang,format(filler_index, '07d'))
                    filler_index += 1
                    if 'ORG' in edl_list:
                        for onename in edl_list['ORG']:
                            
                            for i_sent,sent_x	in	enumerate(ltf_sent_off):
                                if int(sent_x[0]) <= int(onename.split('-')[0])  <= int(sent_x[1]):
                                    y_index = i_sent
                                    break
                            if x_index != y_index:
                                continue
                            
                            if (int(onename.split('-')[0]) <= int(characterOffsetBegin) and int(characterOffsetBegin) <= int(onename.split('-')[1])) or (int(characterOffsetBegin)<=int(onename.split('-')[0]) and int(onename.split('-')[0]) <= int(characterOffsetEnd)):
                                edl_filter_dict[doc_id].append(onename)
                                relation_dict[doc_id].append([edl_list['ORG'][onename][-1], 'GeneralAffiliation.OrganizationWebsite', filler_id, provenance])
                                
#                                print(' '.join(token_text_list))
#                                print('General-Affiliation.Organization-Website: %s\t%s\n'%(edl_list['ORG'][onename][0], text))
                                #print('%s\thttps://tac.nist.gov/tracks/SM-KBP/2018/ontologies/SeedlingOntology#GenAfl.OrgWeb\t%s\t1.0'%(edl_list['ORG'][onename][-1], filler_id ))
                            elif int(onename.split('-')[0]) >= sentence_start and int(onename.split('-')[1]) <= sentence_end:
#                                print(' '.join(token_text_list))
#                                print('General-Affiliation.Organization-Website: %s\t%s\n'%(edl_list['ORG'][onename][0], text))
                                relation_dict[doc_id].append([edl_list['ORG'][onename][-1], 'GeneralAffiliation.OrganizationWebsite', filler_id, provenance])
                             
#                                print('%s\thttps://tac.nist.gov/tracks/SM-KBP/2018/ontologies/SeedlingOntology#GenAfl.OrgWeb\t%s\t1.0'%(edl_list['ORG'][onename][-1], filler_id ))
                elif ner == 'NUMBER':
                    flag_filter = False
                    for filter_token in filter_token_list:
                        if filter_token in text:
                            flag_filter = True
                            break
                    if flag_filter == True:
                        continue

                    #filler_dict[doc_id]['NUMBER'].append([text, characterOffsetBegin, characterOffsetEnd, filler_index])
                    
                    
                    filler_dict[doc_id]['VAL'].append([text, characterOffsetBegin, characterOffsetEnd, format(filler_index, '07d')])
                    filler_id = ':Filler_%s_%s'%(lang,format(filler_index, '07d'))
                    val_flag = False
                    if index_end <len(token_list):

                        
                        for ner_type in edl_list:
                            #if ner_type not in ['VEH','WEA']:
                            #    continue
                            for onename in edl_list[ner_type]:
                                for i_sent,sent_x   in      enumerate(ltf_sent_off):
                                    if int(sent_x[0]) <= int(onename.split('-')[0])  <= int(sent_x[1]):
                                        y_index = i_sent
                                        break
                                if x_index != y_index:
                                    continue
                                
                                if (int(onename.split('-')[0]) - int(characterOffsetEnd)  <= 2) and (int(onename.split('-')[0]) -int(characterOffsetEnd) > 0):
                                    relation_dict[doc_id].append([filler_id, 'Measurement.Count', edl_list[ner_type][onename][-1], provenance])
                                 
#                                    print(' '.join(token_text_list))
#                                    print('Measurement.Count: %s\t%s\n'%(text, edl_list[ner_type][onename][0]))
                                    ######filler_dict[doc_id]['VAL'].append([text+' '+token_list[index_end][0], characterOffsetBegin, token_list[index_end][2]])
                                    #print('%s\thttps://tac.nist.gov/tracks/SM-KBP/2018/ontologies/SeedlingOntology#Measurement.Count\t%s\t1.0'%(edl_list[ner_type][onename][-1], filler_id ))
                                    #print([text+' '+edl_list['VEH'][onename][0], characterOffsetBegin, token_list[index_end][2]])
                                    ###print(doc, ner_type, text, edl_list[ner_type][onename][0],'|||', article[int(characterOffsetBegin): int(onename.split('-')[1])+1])
                                                                            
                        for one_unit in unit_gaz:
                            if token_list[index_end][0].lower() == one_unit.lower():
                                #print(text,token_list[index_end][0], one_unit)
                                filler_dict[doc_id]['VAL'].append([text, characterOffsetBegin, token_list[index_end][2]-1, format(filler_index, '07d') ])
                                ######filler_dict[doc_id]['VAL'].append([text+' '+token_list[index_end][0], characterOffsetBegin, token_list[index_end][2]])
                                val_flag = True
                                continue
                    if val_flag == False:
                        filler_dict[doc_id]['VAL'].append([text, characterOffsetBegin, characterOffsetEnd, format(filler_index, '07d') ])
                                                                            
                    filler_index += 1
#                        elif 'WEA' in edl_list:
#                            for onename in edl_list['WEA']:
#                                if (int(onename.split('-')[0]) - int(characterOffsetEnd)  <= 2) and (int(onename.split('-')[0]) -int(characterOffsetEnd) > 0):
#                                    #print([text+' '+edl_list['WEA'][onename][0], characterOffsetBegin, token_list[index_end][2]])
#                                    print(doc, 'wea', text, edl_list['WEA'][onename][0], '|||', article[int(characterOffsetBegin): int(onename.split('-')[1])])
                            
                elif ner == 'MONEY':
                    filler_dict[doc_id]['MON'].append([text, characterOffsetBegin, characterOffsetEnd, format(filler_index, '07d')])
                    filler_index += 1
                #elif ner == 'ORDINAL':
                #    
                #    
                #    filler_dict[doc_id]['ORDINAL'].append([text, characterOffsetBegin, characterOffsetEnd, filler_index])
                #    filler_index += 1
                elif ner == 'PERCENT':
                    #print(text, characterOffsetBegin, characterOffsetEnd)
                    filler_dict[doc_id]['VAL'].append([text, characterOffsetBegin, characterOffsetEnd, format(filler_index, '07d')])
                    filler_index += 1
                elif ner == 'TITLE':
                    filler_dict[doc_id]['TTL'].append([text, characterOffsetBegin, characterOffsetEnd, format(filler_index, '07d')])
                    filler_index += 1
#                    print([text, characterOffsetBegin, characterOffsetEnd])
    return filler_dict, edl_filter_dict, relation_dict

def read_edl(edl_path):
    edl_dict = {}
    edl_type_dict = {}

    
    with open(edl_path) as f:
        lines = f.readlines()
    for line in lines:
        if len(line.strip().split('\t')) < 3:
            continue
        if line.strip().split('\t')[1] == 'type':
            edl_type_dict[line.strip().split('\t')[0]] = line.strip().split('\t')[2]
        elif 'mention' in line.strip().split('\t')[1]:
            if line.strip().split('\t')[3].split(':')[0] not in edl_dict:

                edl_dict[line.strip().split('\t')[3].split(':')[0]] = {}
            if edl_type_dict[line.strip().split('\t')[0]] not in edl_dict[line.strip().split('\t')[3].split(':')[0]]:
                edl_dict[line.strip().split('\t')[3].split(':')[0]][edl_type_dict[line.strip().split('\t')[0]]] = {}
            edl_dict[line.strip().split('\t')[3].split(':')[0]][edl_type_dict[line.strip().split('\t')[0]]][line.strip().split('\t')[3].split(':')[-1]] = [line.strip().split('\t')[2][1:-1], line.strip().split('\t')[3].split(':')[-1], edl_type_dict[line.strip().split('\t')[0]], line.strip().split('\t')[0]]
            #edl_dict[line.strip().split('\t')[3].split(':')[0]][line.strip().split('\t')[3].split(':')[-1]] = [line.strip().split('\t')[2][1:-1], line.strip().split('\t')[3].split(':')[-1], edl_type_dict[line.strip().split('\t')[0]]] 
    return edl_dict

def filler_en(filler_lines, output_path, title_path):
    # input_path = '/nas/data/m1/lud2/AIDA/dryrun/20190801/filler/en/filler.cs'
    # output_path = '/nas/data/m1/lud2/AIDA/dryrun/20190801/filler/en/filler_cleaned.cs'

    title_path = os.path.join(CURRENT_DIR, 'Title.lst')

    with open(title_path) as f:
        lines = f.readlines()

    title_set = set()

    for line in lines:
        title_set.add(line.strip().lower())



    # with open(input_path) as f:
    #     lines = f.readlines()




    fileter_cache = set()
    filler_type_dcit = {}
    for line in filler_lines:
        if line.strip().split('\t')[1] == 'type':
            filler_type_dcit[line.strip().split('\t')[0]] = line.strip().split('\t')[2]
        if filler_type_dcit[line.strip().split('\t')[0]]!='TTL':
            continue
        if 'mention' not in line.strip().split('\t')[1]:
            continue
        if line.strip().split('\t')[2][1:-1].lower() not in title_set:
            fileter_cache.add(line.strip().split('\t')[0])

    f_out = open(output_path,'w')



    tmp = set()
    # with open(input_path) as f:
    #     lines = f.readlines()
    flag = True
    countx = 0
    for line in filler_lines:
        if line.strip().split('\t')[1]=='type':
            
            if line.strip().split('\t')[0] in tmp:
                flag = False
            else:
                tmp.add(line.strip().split('\t')[0])
                flag = True
        if flag == False:
            continue
        #    print(line)
        if line.strip().split('\t')[0] in fileter_cache:
            #print(line)
            continue
        if line.strip().split('\t')[1] == 'type':
            countx += 1
        #if line.strip().split('\t')[2] == 'TME':
        #    tmp.add(line.strip().split('\t')[0])
        f_out.write('%s'%line)


    f_out.close()

def filler_other(filler_lines, output_path, title_path):
    # input_path = '/nas/data/m1/lud2/AIDA/eval/y1/v1/filler/ru_hypo/filler.cs'
    # output_path = '/nas/data/m1/lud2/AIDA/eval/y1/v1/filler/ru_hypo/filler_cleaned.cs'

    title_path = os.path.join(CURRENT_DIR, 'Title.lst')

    with open(title_path) as f:
        lines = f.readlines()

    title_set = set()

    for line in lines:
        title_set.add(line.strip().lower())



    fileter_cache = set()
    filler_type_dcit = {}
    for line in filler_lines:

        # if line.split('\t')[0] == 'Entity_EDL_0001393':
        #     print(line,'$$$')
        if line.strip().split('\t')[1] == 'type':
            filler_type_dcit[line.strip().split('\t')[0]] = line.strip().split('\t')[2]
        if filler_type_dcit[line.strip().split('\t')[0]]!='TTL':
            continue
        if 'mention' not in line.strip().split('\t')[1]:
            continue
        if line.strip().split('\t')[2][1:-1].lower() not in title_set:
            fileter_cache.add(line.strip().split('\t')[0])


        

    f_out = open(output_path,'w')



    tmp = set()
  
    countx = 0
    for line in filler_lines:
        if line.strip().split('\t')[0] in tmp:
            #print(line)
            continue
        if line.strip().split('\t')[0] in fileter_cache:
            #print(line)
            continue
        # if line.strip().split('\t')[1] == 'type' and line.strip().split('\t')[2] != 'TME':
        #     tmp.add(line.strip().split('\t')[0])
        #     continue
        if line.strip().split('\t')[1] == 'type':
            countx += 1
        f_out.write('%s'%line)


    f_out.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'filler generation')
    parser.add_argument('--corenlp_dir', help='directory of the corenlp results')
    parser.add_argument('--lang', default='en', help='language of the input docs, 2 digit')
    parser.add_argument('--ltf_dir', help='directory of the ltf files')
    parser.add_argument('--edl_path',  help='path of the cs file that contains the edl outputs')
    parser.add_argument('--text_dir',  help='directory of the rsd files')
    parser.add_argument('--units_path', default='units_clean.txt',help='keyword list of units')
    parser.add_argument('--path_relation', help='location of the output file for relation')
    parser.add_argument('--path_filler',  help='location of the output file for filler')
    parser.add_argument('--title_path', default='Title.lst',help='keyword list of the titles')
    args = parser.parse_args()

    # corenlp_dir = '/nas/data/m1/lud2/AIDA/dryrun/20190801/corenlp/en'
    # ltf_dir = '/nas/data/m1/lim22/aida2019/nyt/source/sample_ltf'
    # edl_path = '/nas/data/m1/panx2/tmp/aida/eval/2019/en/nyt_sample/en.linking.cs'
    # #edl_path = '/nas/data/m1/lim22/aida2019/TA1b_eval/E101_PT003/ru_all/edl/merged.cs'
    # #edl_path = '/nas/data/m1/lim22/aida2019/i1/en/edl/merged.cs'
    # text_dir = '/nas/data/m1/lim22/aida2019/nyt/source/sample_rsd'
    # units_path = 'units_clean.txt'
    # args.path_relation = '/nas/data/m1/lud2/AIDA/dryrun/20190801/new_relation/en/new_relation.cs'
    #units_path = 'units.txt'
    #output_path = '/data/m1/lud2/AIDA/pilot/results/en/timex/pilot_timex_en.cs'
    #output_dir = '/data/m1/lud2/AIDA/pilot/results/en/timex/seperate/'


    #corenlp_dir = '/nas/data/m1/lud2/AIDA/pilot/pilot/corenlp_asr'
    #edl_path = '/nas/data/m1/panx2/tmp/aida/eval/2018/en/0912_asr/en.linking.corf.cs'
    #text_dir = '/data/m1/AIDA_Data/aida2018/evaluation/source/en_asr_rsd/'
    #units_path = 'units_clean.txt'


    edl_dict = read_edl(args.edl_path)
    ltf_dict = read_ltf(args.ltf_dir)
    unit_gaz = load_unit_gaz(os.path.join(CURRENT_DIR, args.units_path))
    
                                                                            

    filler_dict, edl_filter_dict, relation_dict = whole_generate(args.corenlp_dir, args.text_dir, unit_gaz, edl_dict, ltf_dict, args.lang.upper())

    # f_filler = open('/nas/data/m1/lud2/AIDA/dryrun/20190801/filler/en/filler.cs','w')
    #f_filler = open('/data/m1/lud2/AIDA/pilot/results/filler/asr/filler_en.cs','w')
    lines_filler = []
    for doc in filler_dict:
        for filler_type in filler_dict[doc]:

            for one_filler in filler_dict[doc][filler_type]:
            
                #f_filler.write(':Filler_ENG_%s\ttype\t%s\n'%(one_filler[3], filler_type))
                #f_filler.write(':Filler_ENG_%s\tmention\t%s\t%s\n'%(one_filler[3], '"'+one_filler[0]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))
                #print(':Filler_ENG_%s\ttype\t%s'%(one_filler[3], filler_type))
                #print(':Filler_ENG_%s\tmention\t%s\t%s'%(one_filler[3], '"'+one_filler[0]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))
                if filler_type == 'TME':
                    # f_filler.write(':Filler_ENG_%s\ttype\t%s\n'%(one_filler[3], filler_type))
                    # f_filler.write(':Filler_ENG_%s\tcanonical_mention\t%s\t%s\t1.0\n'%(one_filler[3], '"'+one_filler[0][0]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))
                    # f_filler.write(':Filler_ENG_%s\tmention\t%s\t%s\t1.0\n'%(one_filler[3], '"'+one_filler[0][0]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))
                    # f_filler.write(':Filler_ENG_%s\tnormalized_mention\t%s\t%s\t1.0\n'%(one_filler[3], '"'+one_filler[0][1]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))

                    lines_filler.append(':Filler_%s_%s\ttype\t%s\n'%(args.lang.upper(),one_filler[3], filler_type))
                    lines_filler.append(':Filler_%s_%s\tcanonical_mention\t%s\t%s\t1.0\n'%(args.lang.upper(),one_filler[3], '"'+one_filler[0][0]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))
                    lines_filler.append(':Filler_%s_%s\tmention\t%s\t%s\t1.0\n'%(args.lang.upper(),one_filler[3], '"'+one_filler[0][0]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))
                    lines_filler.append(':Filler_%s_%s\tnormalized_mention\t%s\t%s\t1.0\n'%(args.lang.upper(),one_filler[3], '"'+one_filler[0][1]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))
                
                else:
                    # f_filler.write(':Filler_ENG_%s\ttype\t%s\n'%(one_filler[3], filler_type))
                    # f_filler.write(':Filler_ENG_%s\tcanonical_mention\t%s\t%s\t1.0\n'%(one_filler[3], '"'+one_filler[0]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))
                    # f_filler.write(':Filler_ENG_%s\tmention\t%s\t%s\t1.0\n'%(one_filler[3], '"'+one_filler[0]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))

                    lines_filler.append(':Filler_%s_%s\ttype\t%s\n'%(args.lang.upper(),one_filler[3], filler_type))
                    lines_filler.append(':Filler_%s_%s\tcanonical_mention\t%s\t%s\t1.0\n'%(args.lang.upper(),one_filler[3], '"'+one_filler[0]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))
                    lines_filler.append(':Filler_%s_%s\tmention\t%s\t%s\t1.0\n'%(args.lang.upper(),one_filler[3], '"'+one_filler[0]+'"', doc+':'+str(one_filler[1])+'-'+str(one_filler[2])))
    # f_filler.close()


    f_relation = open(args.path_relation,'w')
    for doc in relation_dict:
        for one_relation in relation_dict[doc]:
            # print(one_relation)
            f_relation.write('%s\t%s\t%s\t%s\t1.0\n'%(one_relation[0], one_relation[1], one_relation[2], one_relation[3]))
    f_relation.close()

    if args.lang == 'en':
        filler_en(lines_filler, args.path_filler, args.title_path)
    else:
        filler_other(lines_filler, args.path_filler, args.title_path)
