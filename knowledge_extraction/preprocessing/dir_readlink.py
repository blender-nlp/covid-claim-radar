import os
import sys
import codecs
import argparse

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Final output to ColdStart++ including all components')
    parser.add_argument("dir", help="dir")
    parser.add_argument('output_file', help='output_file')
    parser.add_argument('--stanford_corenlp', default=None, type=str, help='stanford_corenlp', required=False)
    
    args = parser.parse_args()

    dir = args.dir
    output_file = args.output_file
    stanford_corenlp = args.stanford_corenlp

    with codecs.open(output_file, 'w', encoding='utf8') as writer:
        if os.path.exists(dir):
            for file in os.listdir(os.path.join(dir)):
                if stanford_corenlp is not None:
                    staford_file = os.path.join(stanford_corenlp, file+'.json')
                    if os.path.exists(staford_file):
                        continue
                writer.write(os.path.join(dir, file))
                writer.write('\n')