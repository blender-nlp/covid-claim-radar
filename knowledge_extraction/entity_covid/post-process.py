import argparse
parser = argparse.ArgumentParser(description='Choose Language')
parser.add_argument('--entity', type=str,
                    help='entity file')
args = parser.parse_args()

path = args.entity

dic = {}
ent2keyline = {}
with open(path,'r') as f:
    line1 = f.readline().strip()
    line2 = f.readline().strip()
    line = f.readline().strip()
    while line:
        if line.split('\t')[1]=='type':
            line = line.replace(' ','\t')
            if len(line.split('\t'))!=4:
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
    f.write(line1+'\n')
    f.write(line2+'\n')
    for key,vals in dic.items():
        for val in vals:
            f.write(val+'\n')