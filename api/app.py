import os
import traceback

from flask import Flask, jsonify, request
import argparse
import codecs
from rsd2ltf import rsd2ltf
from copy import deepcopy
from tqdm import tqdm
import requests
import json
from transformers import pipeline
import csv

app = Flask(__name__)


def run_claimbuster(input_data):
    api_key='182fa6df16814a06ba5d12f7b30d85af'
    api_endpoint = "https://idir.uta.edu/claimbuster/api/v2/score/text/sentences/"
    request_headers = {"x-api-key": api_key}
    for doc_id in tqdm(input_data):
        for i,item in tqdm(enumerate(input_data[doc_id])):
            payload = {"input_text": item["sentence"]}
            api_response = requests.post(url=api_endpoint, json=payload, headers=request_headers)
            output = api_response.json()
            print(output)
            input_data[doc_id][i]["claimbuster_score"] = max([float(r["score"]) for r in output["results"]])
    
    return input_data

def run_qa_topic_model_by_schema(claimbuster_output):    
    final_output = dict()
    sub_topic_mapping = get_old_sub_topic_question_mapping(topics_file)
    final_output["mapping"] = deepcopy(sub_topic_mapping)
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
                result["sub_topic"] = sub_topic_mapping[question]
                output_item["topic_scores"][question] = result
            output[doc_id].append(deepcopy(output_item))
    final_output["output"] = deepcopy(output)
    return final_output

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

def filter_qa_topics(qa_topic_output, topics_file):
    classes = dict()
    threshold = 0.3
    count = 0
    if "mapping" in qa_topic_output:
        sub_topic_mapping = qa_topic_output["mapping"]
        qa_topic_output = qa_topic_output["output"]
    else:
        sub_topic_mapping = get_old_sub_topic_question_mapping(topics_file)


    topic_mapping, template_mapping = get_topic_template_mapping(topics_file)

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
                qa_topic_output[doc_id][index].pop("topic_scores")
                outputs[doc_id].append(deepcopy(qa_topic_output[doc_id][index]))
    print("Total num of sentences: ", count)
    print("Number of extracted claims", sum(classes.values()))
    print(('='* 10) + "Extracted subtopic distribution" + ('='* 10))
    print(classes)
    print('='* 30)
    return outputs


def get_old_sub_topic_question_mapping(topic_file_path):
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


def get_x_variable(claim_sentence_output):
    
    for doc_id in tqdm(claim_sentence_output):
        for index in range(0, len(claim_sentence_output[doc_id])):
            qa_input =  {
                    'question': claim_sentence_output[doc_id][index]["subtopic_question"],
                    'context': claim_sentence_output[doc_id][index]["sentence"]
                }
            try:
                result = nlp_attribute(qa_input)
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

def get_claim_spans(claim_object_output):
    
    for doc_id in tqdm(claim_object_output):
        for index in range(0, len(claim_object_output[doc_id])):
            qa_input =  {
                    'question': "What is being claimed?",
                    'context': claim_object_output[doc_id][index]["sentence"]
                }
            try:
                result = nlp_attribute(qa_input)
                claim_object_output[doc_id][index]["claim_span_start"] = result["start"]
                claim_object_output[doc_id][index]["claim_span_end"] = result["end"]
            except:
                claim_object_output[doc_id][index]["claim_span_start"] = 0
                claim_object_output[doc_id][index]["claim_span_end"] = len(claim_object_output[doc_id][index]["sentence"])

            claim_object_output[doc_id][index]["claim_span_text"] = claim_object_output[doc_id][index]["sentence"][claim_object_output[doc_id][index]["claim_span_start"]:claim_object_output[doc_id][index]["claim_span_end"]]

    return claim_object_output

def run_qa_claimer(claim_span_output, rsd_content):
    for doc_id in tqdm(claim_span_output):
        for index in range(0, len(claim_span_output[doc_id])):
            question = "who said that " + claim_span_output[doc_id][index]["claim_span_text"].strip() + " ?"
            doc_text = rsd_content
            full_doc_input = {
                "question": question,
                "context": doc_text
            }
            full_doc_output = nlp_attribute(full_doc_input)
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

@app.route('/claim', methods=['POST', 'GET'])
def tagging():
    try:
        if request.method == "GET":
            args = request.args
        else:
            args = request.form
            if not args:
                args = request.get_json(force=True)
        rsd_str = args['rsd']
        # rsd to ltf
        # rsd_str = codecs.open(rsd_f, 'r', 'utf-8').read()

        # doc_id = os.path.basename(rsd_f).replace(extension, '')
        doc_id = 'test'
        seg_option = 'nltk+linebreak'
        tok_option = 'nltk_wordpunct'
        re_segment = False
        mytree = rsd2ltf(rsd_str, doc_id, seg_option, tok_option,
                            re_segment)
        # read ltf
        # mytree = mytree.getroot()
        nodes = mytree.findall("DOC")[0].findall("TEXT")[0].findall("SEG")
        # doc_id = mytree.getroot().findall("DOC")[0].get("id")
        
        data = list()
        all_sent_data = dict()
        for node in nodes:
            item = dict()
            item["segment_id"] = node.get("id")
            item["start_char"] = int(node.get("start_char"))
            item["end_char"] = int(node.get("end_char"))
            item["sentence"] = node.findall("ORIGINAL_TEXT")[0].text
            data.append(deepcopy(item))
        all_sent_data[doc_id] = deepcopy(data)
        # tagging claims
        # run the claimbuster system to get the claimbuster scores
        claimbuster_output = run_claimbuster(all_sent_data)

        topic_output_unfiltered = run_qa_topic_model_by_schema(claimbuster_output)
        topic_output = filter_qa_topics(topic_output_unfiltered, topics_file)

        x_output = get_x_variable(topic_output)

        # claim_span_output = get_claim_spans(x_output)
        # qa_claimer_output_ = run_qa_claimer(claim_span_output, rsd_str)
        # qa_claimer_output = get_claimer(qa_claimer_output_)
        
        return jsonify(x_output)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/claim_all', methods=['POST', 'GET'])
def tagging_all():
    try:
        if request.method == "GET":
            args = request.args
        else:
            args = request.form
            if not args:
                args = request.get_json(force=True)
        rsd_str = args['rsd']
        # rsd to ltf
        # rsd_str = codecs.open(rsd_f, 'r', 'utf-8').read()

        # doc_id = os.path.basename(rsd_f).replace(extension, '')
        doc_id = 'test'
        seg_option = 'nltk+linebreak'
        tok_option = 'nltk_wordpunct'
        re_segment = False
        mytree = rsd2ltf(rsd_str, doc_id, seg_option, tok_option,
                            re_segment)
        # read ltf
        # mytree = mytree.getroot()
        nodes = mytree.findall("DOC")[0].findall("TEXT")[0].findall("SEG")
        # doc_id = mytree.getroot().findall("DOC")[0].get("id")
        
        data = list()
        all_sent_data = dict()
        for node in nodes:
            item = dict()
            item["segment_id"] = node.get("id")
            item["start_char"] = int(node.get("start_char"))
            item["end_char"] = int(node.get("end_char"))
            item["sentence"] = node.findall("ORIGINAL_TEXT")[0].text
            data.append(deepcopy(item))
        all_sent_data[doc_id] = deepcopy(data)
        # tagging claims
        # run the claimbuster system to get the claimbuster scores
        claimbuster_output = run_claimbuster(all_sent_data)

        topic_output_unfiltered = run_qa_topic_model_by_schema(claimbuster_output)
        topic_output = filter_qa_topics(topic_output_unfiltered, topics_file)

        x_output = get_x_variable(topic_output)

        claim_span_output = get_claim_spans(x_output)
        qa_claimer_output_ = run_qa_claimer(claim_span_output, rsd_str)
        qa_claimer_output = get_claimer(qa_claimer_output_)
        
        return jsonify(qa_claimer_output)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--topics_file', type=str, help="Path to the list of claim topics")
    parser.add_argument('--claimbuster_key', type=str, help="API key for claimbuster")
    parser.add_argument('--input_dir', type=str, help="Path to the input directory")
    parser.add_argument('--output_dir', type=str, help="Path to the output json file")
    parser.add_argument('--topic_model_path', type=str, help="Path to the topic detection QA model")
    parser.add_argument('--attribute_model_path', type=str, help="Path to the QA model to extract other attributes")
    parser.add_argument("--use_gpu", action='store_true', help="whether to use the GPU")
    parser.add_argument("--claim_detection_only", action='store_true', help="whether to only run the claim detection part")
    args = parser.parse_args()

    # # run the QA system to get the topic scores
    # if not os.path.exists(os.path.join(args.output_dir + "qa_topic_output.json")):
    #     print("Running QA topic filtering")
    #     qa_topic_output = run_qa_topic_model_by_schema(args, claimbuster_output)
    #     json.dump(qa_topic_output, open(os.path.join(args.output_dir + "qa_topic_output.json"), "w"), indent=4)
    # else:
    #     qa_topic_output = json.load(open(os.path.join(args.output_dir + "qa_topic_output.json")))
    # # filter the claims using the topic scores from the QA system
    # claim_sentence_output = filter_qa_topics(qa_topic_output, args.topics_file)

    gpu = False
    # Preload models
    model_path = './topic_model'
    nlp = pipeline('question-answering', model=model_path, tokenizer=model_path)
    model_path_attribute = './attribute_model'
    nlp_attribute = pipeline('question-answering', model=model_path_attribute, tokenizer=model_path_attribute)

    topics_file = './sample_topics.tsv'

    app.run(host='0.0.0.0', port=5500)
