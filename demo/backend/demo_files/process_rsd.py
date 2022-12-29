import os
import json

if not os.path.exists('processed_rsd'):
    os.makedirs('./processed_rsd')

for dir_ in ['rsd_en','rsd_es','rsd_ru']:
    rsd_files = os.listdir(dir_)

    for rsd_file in rsd_files:
        rsd_path = dir_+'/'+rsd_file
        with open(rsd_path,'r') as f:
            data = f.read()
            # data = data.replace('\n','<br />')
        new_data = [{'Data':data}]
        with open('./processed_rsd/'+rsd_file+'.json','w') as f:
            json.dump(new_data,f)
