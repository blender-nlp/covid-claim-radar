import json
from collections import defaultdict
import torch
import clip
from PIL import Image
import os

# import torch

# from PIL import Image
# import os

# from model_clip import build_model
# from clip import _transform

claim_json = '/shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/en/ttl/claim_all.json'
claim_data = json.load(open(claim_json))

claim_id_list = [
    'claim_2022-03-05_h_6ecbb18224dc7ef55170557a28047547_0', 
    'claim_2022-03-24_h_645231ff1bbea185e4ea5c10732c4ac3_0',
    'claim_2022-03-16_h_450fa6006a56983e64739cd5e3a81665_0',
    'claim_2022-05-10_h_dbfaf377a2e604d110f97d2aaeac8904_0',
    'claim_2022-03-09_h_0b4b3ef39a571967f642e50520540e1b_0'
    ]

date_image = '/shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/rawdata/cnn_ukraine_image'
# /shared/nas/data/m1/manling2/ibm/graph_sum_text/data/cnn_ukraine/cnn_ukraine_image

meta_data = '/shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/rawdata/meta_data.json'

json_data = json.load(open(meta_data))

image_date_dict = defaultdict(list)
id2date = dict()
for id in json_data:
    date = json_data[id]['dateTimeline']
    image = os.path.join('/shared/nas/data/m1/manling2/aida_docker_test/covid-claim-radar/data/ukraine_v2/rawdata/cnn_ukraine_image', id +'.jpg') #json_data[id]['dateTimeline']
    image_date_dict[date].append(image)
    id2date[id] = date
# print(image_date_dict)

claim_id_dict = defaultdict()
for doc_id in claim_data:
    for claim in claim_data[doc_id]:
        claim_id = claim['claim_id']
        claim_context = claim['context']
        claim_sentence = claim['sentence']
        claim_id_dict[claim_id] = claim_sentence

# device = "cuda" if torch.cuda.is_available() else "cpu"
# ckpt_path = '/shared/nas/data/m1/manling2/clip-event/checkpoint/RN50.pt'
# # ckpt_path = '/shared/nas/data/m1/manling2/clip-event/checkpoint/ViT-B-32.pt'
# model = torch.jit.load(ckpt_path, map_location=device) #.eval()
# state_dict = None
# model = build_model(state_dict or model.state_dict()).to(device)
# preprocess = _transform(model.visual.input_resolution)

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load('/shared/nas/data/m1/manling2/clip-event/checkpoint/ViT-B-32.pt', device=device)

for claim_id in claim_id_list:
    claim_sentence = claim_id_dict[claim_id]
    text = clip.tokenize([claim_sentence]).to(device)
    print(text.size())
    date = id2date[id]
    image_list_date = image_date_dict[date]
    image_list = list()
    for image in image_list_date:
        image_emb = preprocess(Image.open(image)).to(device)
        image_list.append(image_emb)
    image_matrix = torch.stack(image_list, dim=0)
    print(image_matrix.size())
    with torch.no_grad():
        # image_features = model.encode_image(image_matrix)
        # text_features = model.encode_text(text)

        logits_per_image, logits_per_text = model(image_matrix, text)
        probs = logits_per_text.softmax(dim=-1)
        scores, pred_idx = torch.max(probs, dim=-1)
        pred_image = image_list_date[pred_idx.item()]
        print(pred_idx, pred_image)
        print('pred_idx', pred_idx.size())