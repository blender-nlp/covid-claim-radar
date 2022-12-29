import glob
import os
import json
from tqdm import tqdm
import argparse


INPUT_DIR = "./input"
INPUT_TYPE = ["doc", "combined"][1]
RESOURCE_DIR = "./resources/models/covid"
OUTPUT_DIR = "./output"
parser = argparse.ArgumentParser()
parser.add_argument("--input_dir", "-i", type=str, default=INPUT_DIR)
parser.add_argument("--output_dir", "-o", type=str, default=OUTPUT_DIR)
parser.add_argument("--input_type", "-t", type=str, default=INPUT_TYPE, choices=["doc", "combined"])
parser.add_argument("--resource_dir", "-r", type=str, default=RESOURCE_DIR)

args = parser.parse_args()

os.makedirs(args.output_dir, exist_ok=True)

os.environ["TRANSFORMERS_CACHE"] = os.path.abspath(os.path.join(args.resource_dir, 'cache'))
from event_detector import EventDetector

def string_assign(input_str, assign_str, start):
    assert start >= 0 and start + len(assign_str) <= len(input_str)
    output_str = input_str[:start] + assign_str + input_str[start + len(assign_str):]
    return output_str

def convert_oneie(oneie):
    out = {}
    out["sent_id"] = oneie["sent_id"]
    out["tokens"] = oneie["tokens"]
    out["token_offsets"] = []
    for token_id in oneie["token_ids"]:
        start, end = token_id.split(":")[1].split("-")
        out["token_offsets"].append([int(start), int(end)+1])
    sentence = " " * (out["token_offsets"][-1][1] - out["token_offsets"][0][0])
    sent_start = out["token_offsets"][0][0]
    for token, (start, end) in zip(out["tokens"], out["token_offsets"]):
        sentence = string_assign(sentence, token, start - sent_start)
    out["sentence"] = sentence
    return out

sentences = []
if args.input_type == "doc":
    json_files = glob.glob(os.path.join(args.input_dir, "*.json"))
    for json_file in tqdm(json_files):
        with open(json_file) as fp:
            data = [json.loads(t) for t in fp]
        sentences.extend([convert_oneie(t) for t in data])
elif args.input_type == "combined":
    json_file = os.path.join(args.input_dir, "oneie.json")
    with open(json_file) as fp:
        all_data = json.load(fp)
    json_data = all_data["oneie"]["en"]["json"]
    for doc_id, doc_str in tqdm(json_data.items()):
        data = [json.loads(t) for t in doc_str.strip().split("\n")]
        sentences.extend([convert_oneie(t) for t in data])

if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)
with open(os.path.join(args.output_dir, "docs.jsonl"), "wt") as fp:
    for t in sentences:
        fp.write(json.dumps(t)+"\n")

ed = EventDetector(args.resource_dir)
data_sentences = [t["sentence"] for t in sentences]
output_triggers = ed(data_sentences)
with open(os.path.join(args.output_dir, "docs.ann.jsonl"), "wt") as fp:
    for t in output_triggers:
        fp.write(json.dumps(t)+"\n")
