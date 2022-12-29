from convert import json_to_cs_aida, json_to_mention_results, bio_to_cfet
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--output_dir", "-o", type=str)
args = parser.parse_args()
ROOT = args.output_dir

json_to_cs_aida(f"{ROOT}/json/", f"{ROOT}/cs/")
json_to_mention_results(f"{ROOT}/json", f"{ROOT}/mention/", file_name='en')
bio_to_cfet(f"{ROOT}/mention/en.nam.bio", f"{ROOT}/mention/en.nam.cfet.json")
