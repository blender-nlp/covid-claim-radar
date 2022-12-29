from re import L
from tempfile import template
import requests
import json
from tqdm import tqdm
from copy import deepcopy
import numpy as np
import argparse
import csv
import glob
import xml.etree.ElementTree as ET
from transformers import pipeline
import csv
import os

def read_all_sents(input_dir):
    files = glob.glob(input_dir + "/ltf/" + "*.ltf.xml")
    all_sent_data = dict()
    for f in files:
        data = list()
        mytree = ET.parse(f)
        nodes = mytree.getroot().findall("DOC")[0].findall("TEXT")[0].findall("SEG")
        doc_id = mytree.getroot().findall("DOC")[0].get("id")
        for node in nodes:
            item = dict()
            item["segment_id"] = node.get("id")
            item["start_char"] = int(node.get("start_char"))
            item["end_char"] = int(node.get("end_char"))
            item["sentence"] = node.findall("ORIGINAL_TEXT")[0].text
            data.append(deepcopy(item))
        all_sent_data[doc_id] = deepcopy(data)
    return all_sent_data

def run_claimbuster(input_data, api_key):
    api_endpoint = "https://idir.uta.edu/claimbuster/api/v2/score/text/sentences/"
    request_headers = {"x-api-key": api_key}
    for doc_id in tqdm(input_data):
        for i,item in tqdm(enumerate(input_data[doc_id])):
            payload = {"input_text": item["sentence"]}
            api_response = requests.post(url=api_endpoint, json=payload, headers=request_headers)
            output = api_response.json()
            input_data[doc_id][i]["claimbuster_score"] = max([float(r["score"]) for r in output["results"]])
    
    return input_data

def get_sub_topic_question_mapping(topic_file_path):
    mapping = dict()
    csv_reader = csv.reader(open(topic_file_path), delimiter='\t')
    for row in csv_reader:
        if len(row) > 2:
            topic = row[1]
            sub_topic = row[2]
            template = row[3]
            if sub_topic.lower().split()[0] in ["who", "what", "when", "where", "why"]:
                question = sub_topic
            else:
                x_found = False
                question_words = list()
                template = template.strip()
                for word in template.split():
                    if not x_found:
                        if word.lower() == "x":
                            x_found = True
                            question_words.append("what")
                        elif "-x" in word.lower():
                            x_found = True
                            rem = word.lower().replace("-x", "")
                            if "/" in rem:
                                rem = rem.split("/")[0]
                            question_words.append("what " + rem)      
                        else:
                            question_words.append(word)             
                    else:
                        question_words.append(word)
                question = " ".join(question_words)

            question = question.replace("COVID-19", "the virus")
            question = question.replace("SARS-COV-2", "the virus")

            mapping[question] = sub_topic
        else:
            sub_topic = row[1]
            question = sub_topic
            question = question.replace("COVID-19", "the virus")
            question = question.replace("SARS-COV-2", "the virus")

            mapping[question] = sub_topic
        # print(sub_topic, "===========", question)
    return mapping

def get_topic_template_mapping(topic_file_path):
    csv_reader = csv.reader(open(topic_file_path), delimiter='\t')
    topic_mapping = dict()
    template_mapping = dict()
    for row in csv_reader:
        if len(row) > 2:
            topic_mapping[row[2]] = row[1]
            template_mapping[row[2]] = row[3]
        else:
            topic_mapping[row[1]] = row[1]
    return topic_mapping, template_mapping

def run_qa_topic_model_by_schema(args, claimbuster_output):
    model_path = args.topic_model_path
    if args.use_gpu:
        nlp = pipeline('question-answering', model=model_path, tokenizer=model_path, device=0)
    else:
        nlp = pipeline('question-answering', model=model_path, tokenizer=model_path)
    
    sub_topic_mapping = get_sub_topic_question_mapping(args.topics_file)
    output = dict()

    for doc_id in tqdm(claimbuster_output):
        output[doc_id] = list()
        for sentence_item in claimbuster_output[doc_id]:
            output_item = deepcopy(sentence_item)
            output_item["topic_scores"] = dict()
            for question in sub_topic_mapping:
                qa_input =  {
                    'question': question,
                    'context': sentence_item["sentence"].strip()
                }
                result = nlp(qa_input)
                output_item["topic_scores"][question] = result
            output[doc_id].append(deepcopy(output_item))

    return output

def filter_qa_topics(qa_topic_output, topics_file_path):
    classes = dict()
    threshold = 0.3
    count = 0

    sub_topic_mapping = get_sub_topic_question_mapping(topics_file_path)
    topic_mapping, template_mapping = get_topic_template_mapping(topics_file_path)

    outputs = dict()
    for doc_id in tqdm(qa_topic_output):
        outputs[doc_id] = list()
        for index in range(0, len(qa_topic_output[doc_id])):
            topic_scores = sorted([(key, qa_topic_output[doc_id][index]["topic_scores"][key]['score']) for key in sub_topic_mapping], key=lambda item: item[1], reverse=True)
            sub_topic = sub_topic_mapping[topic_scores[0][0]]
            count += 1
            if topic_scores[0][1] > threshold:
                if sub_topic not in classes:
                    classes[sub_topic] = 0
                classes[sub_topic] = classes[sub_topic] + 1
                qa_topic_output[doc_id][index]["topic"] = topic_mapping[sub_topic]
                qa_topic_output[doc_id][index]["sub_topic"] = sub_topic
                if sub_topic in template_mapping:
                    qa_topic_output[doc_id][index]["template"] = template_mapping[sub_topic]
                qa_topic_output[doc_id][index]["final_claim_score"] = topic_scores[0][1]
                qa_topic_output[doc_id][index]["subtopic_question"] =  topic_scores[0][0]
                outputs[doc_id].append(deepcopy(qa_topic_output[doc_id][index]))
    print("Total num of sentences: ", count)
    print("Number of extracted claims", sum(classes.values()))
    print(('='* 10) + "Extracted subtopic distribution" + ('='* 10))
    print(classes)
    print('='* 30)
    return outputs

def get_x_variable(claim_sentence_output, args):
    model_path = args.attribute_model_path
    if args.use_gpu:
        nlp = pipeline('question-answering', model=model_path, tokenizer=model_path, device=0)
    else:
        nlp = pipeline('question-answering', model=model_path, tokenizer=model_path)
    
    for doc_id in tqdm(claim_sentence_output):
        for index in range(0, len(claim_sentence_output[doc_id])):
            qa_input =  {
                    'question': claim_sentence_output[doc_id][index]["subtopic_question"],
                    'context': claim_sentence_output[doc_id][index]["sentence"]
                }
            try:
                result = nlp(qa_input)
                claim_sentence_output[doc_id][index]["x_variable"] = result["answer"]
                claim_sentence_output[doc_id][index]["x_variable_start"] = result["start"]
                claim_sentence_output[doc_id][index]["x_variable_end"] = result["end"]
            except:
                claim_sentence_output[doc_id][index]["x_variable"] = "None"
                claim_sentence_output[doc_id][index]["x_variable_start"] = -1
                claim_sentence_output[doc_id][index]["x_variable_end"] = -1
                print("Error extracting claim object for: ", claim_sentence_output[doc_id][index]["sentence"])
                continue

    return claim_sentence_output

def get_claim_spans(claim_object_output, args):
    model_path = args.attribute_model_path
    if args.use_gpu:
        nlp = pipeline('question-answering', model=model_path, tokenizer=model_path, device=0)
    else:
        nlp = pipeline('question-answering', model=model_path, tokenizer=model_path)
    
    for doc_id in tqdm(claim_object_output):
        for index in range(0, len(claim_object_output[doc_id])):
            qa_input =  {
                    'question': "What is being claimed?",
                    'context': claim_object_output[doc_id][index]["sentence"]
                }
            try:
                result = nlp(qa_input)
                claim_object_output[doc_id][index]["claim_span_start"] = result["start"]
                claim_object_output[doc_id][index]["claim_span_end"] = result["end"]
            except:
                claim_object_output[doc_id][index]["claim_span_start"] = 0
                claim_object_output[doc_id][index]["claim_span_end"] = len(claim_object_output[doc_id][index]["sentence"])

            claim_object_output[doc_id][index]["claim_span_text"] = claim_object_output[doc_id][index]["sentence"][claim_object_output[doc_id][index]["claim_span_start"]:claim_object_output[doc_id][index]["claim_span_end"]]

    return claim_object_output

def run_qa_claimer(claim_span_output, args):
    model_path = args.attribute_model_path
    if args.use_gpu:
        nlp = pipeline('question-answering', model=model_path, tokenizer=model_path, device=0)
    else:
        nlp = pipeline('question-answering', model=model_path, tokenizer=model_path)
    
    for doc_id in tqdm(claim_span_output):
        for index in range(0, len(claim_span_output[doc_id])):
            question = "who said that " + claim_span_output[doc_id][index]["claim_span_text"].strip() + " ?"
            doc_text = open(args.input_dir + "/rsd/" + doc_id + ".rsd.txt").read()
            full_doc_input = {
                "question": question,
                "context": doc_text
            }
            full_doc_output = nlp(full_doc_input)
            claim_span_output[doc_id][index]["claimer_debug"] = deepcopy(full_doc_output)
    return claim_span_output

def get_claimer(qa_claimer_output):
    claimer_threshold = 0.01
    for doc_id in qa_claimer_output:
        for index in range(0, len(qa_claimer_output[doc_id])):
            if qa_claimer_output[doc_id][index]["claimer_debug"]["score"] > claimer_threshold:
                qa_claimer_output[doc_id][index]["claimer_text"] = qa_claimer_output[doc_id][index]["claimer_debug"]["answer"]
                qa_claimer_output[doc_id][index]["claimer_start"] = qa_claimer_output[doc_id][index]["claimer_debug"]["start"]
                qa_claimer_output[doc_id][index]["claimer_end"] = qa_claimer_output[doc_id][index]["claimer_debug"]["end"]
                qa_claimer_output[doc_id][index]["claimer_debug"]["extracted_from"] = "full document"
            else:
                qa_claimer_output[doc_id][index]["claimer_text"] = "<AUTHOR>"
                qa_claimer_output[doc_id][index]["claimer_start"] = -1
                qa_claimer_output[doc_id][index]["claimer_end"] = -1
            qa_claimer_output[doc_id][index]["claimer_score"] = qa_claimer_output[doc_id][index]["claimer_debug"]["score"]

    return qa_claimer_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parser')
    parser.add_argument('--topics_file', type=str, help="Path to the list of claim topics")
    parser.add_argument('--claimbuster_key', type=str, help="API key for claimbuster")
    parser.add_argument('--input_dir', type=str, help="Path to the input directory")
    parser.add_argument('--output_dir', type=str, help="Path to the output json file")
    parser.add_argument('--topic_model_path', type=str, help="Path to the topic detection QA model")
    parser.add_argument('--attribute_model_path', type=str, help="Path to the QA model to extract other attributes")
    parser.add_argument("--use_gpu", action='store_true', help="whether to use the GPU")
    parser.add_argument("--claim_detection_only", action='store_true', help="whether to only run the claim detection part")
    args = parser.parse_args()

    # read all sentences from the input ltf files
    print("Reading all sentences")
    input_data = read_all_sents(args.input_dir)
    # run the claimbuster system to get the claimbuster scores
    if not os.path.exists(os.path.join(args.output_dir + "claimbuster.json")):
        print("Running ClaimBuster system")
        claimbuster_output = run_claimbuster(input_data, args.claimbuster_key)
        json.dump(claimbuster_output, open(os.path.join(args.output_dir + "claimbuster.json"), "w"), indent=4)
    else:
        claimbuster_output = json.load(open(os.path.join(args.output_dir + "claimbuster.json")))

    # run the QA system to get the topic scores
    if not os.path.exists(os.path.join(args.output_dir + "qa_topic_output.json")):
        print("Running QA topic filtering")
        qa_topic_output = run_qa_topic_model_by_schema(args, claimbuster_output)
        json.dump(qa_topic_output, open(os.path.join(args.output_dir + "qa_topic_output.json"), "w"), indent=4)
    else:
        qa_topic_output = json.load(open(os.path.join(args.output_dir + "qa_topic_output.json")))
    # filter the claims using the topic scores from the QA system
    claim_sentence_output = filter_qa_topics(qa_topic_output, args.topics_file)

    if not args.claim_detection_only:
        # extract x_variable/claim object
        print("Running X-Variable Detection")
        claim_object_output = get_x_variable(claim_sentence_output, args)
        # extract span of the exact claim within the claim sentences
        print("Running Claim Span Detection")
        claim_span_output = get_claim_spans(claim_object_output, args)
        # run the qa model for claimer detection
        print("Running Claimer Detection")
        qa_claimer_output = run_qa_claimer(claim_span_output, args)
        # final claimer detection
        claimer_output = get_claimer(qa_claimer_output)
        json.dump(claimer_output, open(os.path.join(args.output_dir + "claim_output.json"), "w"), indent=4)


