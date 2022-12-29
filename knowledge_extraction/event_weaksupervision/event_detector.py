import json
import os
import torch
import glob
from transformers import AutoTokenizer, AutoModel
from typing import List
from utils.utils import WSAnnotations
from tqdm import tqdm

os.environ["TOKENIZERS_PARALLELISM"] = "true"


class EventDetector(object):

    def __init__(self, load_path:str="./resources/models/covid"):
        with open(os.path.join(load_path, "label_info.json"), "rt") as fp:
            label_info = json.load(fp)
            self.label2id = {label: info["id"] for label, info in label_info.items()}; self.label2id["NA"] = 0

        th_path = os.path.join(load_path, "label_threshold.json")
        if os.path.exists(th_path):
            with open(th_path, "rt") as fp:
                th = json.load(fp)
        else:
            th = 0.65

        model_path = glob.glob(os.path.join(load_path, "*.th"))
        # print(model_path)
        self.device = {}
        if torch.cuda.is_available():
            ngpus = torch.cuda.device_count()
            for idx, model_path in enumerate(model_path):
                lang = os.path.split(model_path)[-1].split('.')[0]
                self.device[lang] = torch.device(f'cuda:{idx%ngpus}')
        else:
            for idx, model_path in enumerate(model_path):
                lang = os.path.split(model_path)[-1].split('.')[0]
                self.device[lang] = torch.device(f'cpu')

        cluster = {
                lang: torch.load(os.path.join(load_path, f"{lang}.th"), map_location=self.device[lang]) for lang in self.device
                }
        self.cluster_vectors = {lang: v['vector'] for lang, v in cluster.items()}
        self.clusterid2label = {lang: v['id2label'] for lang, v in cluster.items()}

        model_names = {'en': 'bert-large-cased', 'zh': 'bert-base-multilingual-cased'}
        for lang in model_names:
             if lang not in {'en', 'zh'}:
                 model_names[lang] = model_names['zh']
        self.tokenizer = {
                lang: AutoTokenizer.from_pretrained(model_names[lang]) for lang in self.device
                }
        self.model = {
                lang: AutoModel.from_pretrained(model_names[lang]).to(self.device[lang]) for lang in self.device
                }
        self.annotator = {
                lang: WSAnnotations(threshold=th, tokenizer=self.tokenizer[lang], label2id=self.label2id, id2label=self.clusterid2label[lang], uthreshold=th)
                for lang in self.device
                }
        self.batch_size = 32

    def __call__(self, data_sentences:List[str], lang:str='en', output_format='normal'):
        model = self.model[lang]
        tokenizer = self.tokenizer[lang]
        keyword_vectors = self.cluster_vectors[lang]
        annotator = self.annotator[lang]
        nsent = len(data_sentences)
        batch_size = min(self.batch_size, nsent)
        with torch.no_grad():
            model.eval()
            outputs = []
            for ibatch in tqdm(range(0, nsent, batch_size)):
                batch = data_sentences[ibatch:ibatch+batch_size]
                batch_encoding = tokenizer(
                    batch,
                    add_special_tokens=True,
                    is_split_into_words=False,
                    return_tensors='pt',
                    padding='longest')
                batch_encoding_gpu = batch_encoding.to(keyword_vectors.device)
                output = model(**batch_encoding_gpu).last_hidden_state
                output = output / torch.norm(output, dim=-1, keepdim=True)
                score = torch.matmul(output, keyword_vectors.transpose(0, 1)).detach().cpu()
                batch_annotations = annotator.annotate(batch_encoding.to(torch.device('cpu')), score)
                outputs.extend(batch_annotations)
        if outputs[0]['tokens'] is None:
            for sent, ann in zip(data_sentences, outputs):
                ann['tokens'] = sent
        if output_format == 'kg':
            count = 0
            for instance in outputs:
                instance['event_mentions'] = [
                        {
                            "trigger": instance['tokens'][t[0]:t[1]],
                            "trigger_offsets": f"{t[0]}-{t[1]}",
                            "event_offsets": "",
                            "event_extent": "",
                            "mention_id": f"evt_{count + i}"
                            }
                        for i, t in enumerate(instance['annotations'])
                        ]
                count += len(instance['annotations'])
                instance['warning'] = 'mention_id field is only valid w.r.t each call of api (unique within one call). there could be duplicate ids across multiple calls.'
        return outputs
