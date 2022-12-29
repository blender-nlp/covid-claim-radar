import glob
import os
import json
from tqdm import tqdm
import argparse

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


def detect(detector, results):
    sentences = []
    json_data = results["oneie"]["en"]["json"]
    for doc_id, doc_str in tqdm(json_data.items()):
        data = [json.loads(t) for t in doc_str.strip().split("\n")]
        sentences.extend([convert_oneie(t) for t in data])
    data_sentences = [t["sentence"] for t in sentences]
    output_triggers = detector(data_sentences)
    
    return sentences, output_triggers