from .data import IDataset, _to_instance
import json
from nltk.tokenize.treebank import TreebankWordDetokenizer
import numpy as np
import os
import re
import torch
from torch.utils.data import DataLoader
import transformers
from transformers import PreTrainedTokenizerFast, BatchEncoding, AutoTokenizer
from typing import *


def preprocess_func_token(input_file):
    detokenizer = TreebankWordDetokenizer()
    with open(input_file, "rt") as fp:
        data = [json.loads(t) for t in fp]
    data_sentences = [(str(i), detokenizer.detokenize(t['tokens'])) for i, t in enumerate(data)]
    sentences = set()
    data_sentences_no_replica = []
    for d in data_sentences:
        if d[1] not in sentences:
            sentences.add(d[1])
            data_sentences_no_replica.append(d)
    return data_sentences_no_replica


def get_dataset_and_loader(path, label2id:Dict[str, int], method='token', model_name='bert-large-cased', batch_size=8):
    try:
        with open(path, "rt") as f:
            data = json.load(f)
    except Exception as e:
        with open(path, "rt") as f:
            data = [json.loads(line) for line in f]
    if 'annotations' in data[0]:
        for example in data:
            for annotation in example['annotations']:
                if annotation[2].startswith("CND"):
                    annotation[2] = annotation[2][4:]
    instances = _to_instance(data)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    dataset = IDataset(
        instances=instances,
        label2id=label2id,
        setting=method,
        tokenizer=tokenizer,
        max_length=128)
    dataloader = DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        shuffle=False,
        drop_last=False,
        collate_fn=dataset.collate_fn,
        pin_memory=True)
    return dataset, dataloader


class Record(object):
    def __init__(self, percentage=False):
        super().__init__()
        self.value = 0.
        self.num = 0.
        self.percentage = percentage

    def __iadd__(self, val):
        self.value += val
        self.num += 1
        return self

    def reset(self):
        self.value = 0.
        self.num = 0.

    def __str__(self):
        if self.percentage:
            display = f"{self.value / max(1, self.num) * 100:.2f}%"
        else:
            display = f"{self.value / max(1, self.num):.4f}"
        return display

    @property
    def true_value(self,):
        return self.value / max(1, self.num)

    def __eq__(self, other):
        return self.true_value == other.true_value

    def __lt__(self, other):
        return self.true_value < other.true_value

    def __gt__(self, other):
        return self.true_value > other.true_value

    def __ge__(self, other):
        return self.true_value >= other.true_value

    def __le__(self, other):
        return self.true_value <= other.true_value

    def __ne__(self, other):
        return self.true_value != other.true_value

class F1Record(Record):
    def __init__(self):
        super().__init__()
        self.value = np.zeros(3)
    def __iadd__(self, val:Union[Record, np.ndarray]):
        self.value += val
        return self
    def reset(self,):
        self.value = np.zeros(3)
    def __str__(self):
        denom = self.value[0] + self.value[1]
        if denom == 0:
            return f'{0:.4f}'
        else:
            return f'{self.value[2]*2 / denom:.4f}'
    @property
    def true_value(self,):
        denom = self.value[0] + self.value[1]
        if denom == 0:
            return 0
        else:
            return self.value[2]*2 / denom

    @property
    def full_result(self,):
        precision = self.value[2] / max(self.value[1], 1)
        recall = self.value[2] / max(self.value[0], 1)
        f1 = self.value[2] * 2/ max(self.value[0] + self.value[1], 1)
        return precision, recall, f1

    @property
    def named_result(self,):
        precision, recall, f1 = self.full_result
        return {"precision": precision, "recall": recall, "f1":f1}

class F1MetricTag(object):

    NAL_match = re.compile(r'[^A-Z,a-z]')
    BIO_match = re.compile(r'(?P<start>\d+)B-(?P<label>[a-z]+)\s(?:(?P<end>\d+)I-(?P=label)\s)*')
    IO_match = re.compile(r'(?P<start>\d+)I-(?P<label>[a-z]+)\s(?:(?P<end>\d+)I-(?P=label)\s)*')

    def __init__(self, pad_value:int, ignore_labels:Optional[Union[int, List[int], Set[int]]], label2id:Dict[str, int], tokenizer:Optional[PreTrainedTokenizerFast]=None, save_dir:Optional[str]=None, save_output:bool=True, save_annotation:bool=True, return_annotation:bool=False) -> None:
        if isinstance(ignore_labels, int):
            self.ignore_labels = {ignore_labels}
        elif ignore_labels is None:
            self.ignore_labels = set()
        else:
            self.ignore_labels = set(ignore_labels)
        self.pad_value = pad_value
        self.save_dir = save_dir
        self.label2id = label2id
        self.id2nickname = {}
        self.nickname2label = {}
        self.id2tag = {}
        for label, id_ in label2id.items():
            uncased_label = self.NAL_match.sub('', label).lower()
            while uncased_label in self.nickname2label:
                uncased_label += 'a'
            self.nickname2label[uncased_label] = label
            self.id2nickname[id_] = uncased_label
        for id_, nickname in self.id2nickname.items():
            if id_ in self.ignore_labels:
                self.id2tag[id_] = 'O'
            else:
                self.id2tag[id_] = f'I-{nickname}'
        self.tokenizer = tokenizer
        self.save_annotation = save_annotation
        self.save_output = save_output
        self.return_annotation = return_annotation

    def _merge_consecutive_two_token(self, first_input_id:int, second_input_id:int):
        first_input_id = int(first_input_id)
        second_input_id = int(second_input_id)
        if isinstance(self.tokenizer, transformers.RobertaTokenizerFast):
            return (not self.tokenizer.convert_ids_to_tokens(second_input_id).startswith(chr(288))) and \
                self.tokenizer.convert_ids_to_tokens(first_input_id)[-1].isalpha() and \
                self.tokenizer.convert_ids_to_tokens(second_input_id)[0].isalpha()
        elif isinstance(self.tokenizer, transformers.BertTokenizerFast):
            return self.tokenizer.convert_ids_to_tokens(second_input_id).startswith('##')

    @classmethod
    def find_offsets(cls, seq_str:str, match:re.Pattern):
        annotations = []
        for annotation in match.finditer(seq_str):
            start = int(annotation.group('start'))
            label = annotation.group('label')
            end = annotation.group('end')
            end = start + 1 if end is None else int(end) + 1
            annotations.append((start, end, label))
        return annotations

    def collect_spans(self, sequence:str) -> Set[Tuple[int, int, str]]:
        spans = self.find_offsets(sequence, self.IO_match)
        label_spans = set()
        for span in spans:
            label_spans.add((span[0], span[1], self.nickname2label[span[2]]))
        return label_spans

    def _preprocess(self, array:Union[List[Union[List[List[int]], List[int], torch.Tensor, np.ndarray]], torch.Tensor, np.ndarray]):
        if isinstance(array, list):
            if isinstance(array[0], list):
                if isinstance(array[0][0], list):
                    array = [np.array(sequence) for batch in array for sequence in batch]
                else:
                    array = [np.array(sequence) for sequence in array]
            elif isinstance(array[0], np.ndarray):
                if len(array[0].shape) == 2:
                    array = [sequence for batch in array for sequence in batch]
                elif len(array[0].shape) == 1:
                    pass
                else:
                    raise ValueError(f"Cannot parse List of ndarray of shape {array[0].shape}.")
            elif isinstance(array[0], torch.Tensor):
                if len(array[0].size()) == 2:
                    array = [sequence.numpy() for batch in array for sequence in batch]
                elif len(array[0].shape) == 1:
                    array = [sequence.numpy() for sequence in array]
                else:
                    raise ValueError(f"Cannot parse List of pytorch tensor of size {array[0].size()}.")
        elif isinstance(array, np.ndarray):
            pass
        elif isinstance(array, torch.Tensor):
            array = array.numpy()
        sequences = []
        for idx, sequence in enumerate(array):
            sequence = sequence[sequence!=self.pad_value]
            sequences.append(" ".join([f'{offset}{self.id2tag[token]}' for offset, token in enumerate(sequence)]) + " ")
        return sequences

    def annotate(self, predictions:List[Union[List[Tuple[int, int, str]], Set[Tuple[int, int, str]]]], encodings:Union[List[BatchEncoding], BatchEncoding],save:bool=True) -> None:
        fw = None
        if save: fw = open(os.path.join(self.save_dir, "prediction.jsonl"), "wt")
        corpus_annotations = []
        for i, prediction in enumerate(predictions):
            if isinstance(encodings, list):
                encoding = encodings[i]
            annotations = []
            for annotation in prediction:
                start_pt = annotation[0]
                end_pt = annotation[1]
                if isinstance(encodings, list):
                    start = encoding.token_to_chars(start_pt).start
                    end = encoding.token_to_chars(end_pt-1).end
                else:
                    start = encodings.token_to_chars(i, start_pt).start
                    end = encodings.token_to_chars(i, end_pt-1).end
                annotations.append([start, end, annotation[2]])
            if save:
                fw.write(json.dumps({"annotations": annotations})+"\n")
            corpus_annotations.append(annotations)
        if save: fw.close()
        return corpus_annotations

    def fix_spans(self, predictions:List[Union[List[Tuple[int, int, str]], Set[Tuple[int, int, str]]]], encodings:List[BatchEncoding]) -> List[Set[Tuple[int, int, str]]]:
        fixed = []
        for i, prediction in enumerate(predictions):
            encoding = encodings[i]
            input_ids = getattr(encoding, 'input_ids', getattr(encoding, 'ids', None))
            annotations = set()
            for annotation in prediction:
                start_pt = annotation[0]
                end_pt = annotation[1]
                if start_pt >= len(input_ids) - 1 or start_pt == 0 or end_pt >= len(input_ids):
                    continue
                while start_pt > 1 and self._merge_consecutive_two_token(input_ids[start_pt-1], input_ids[start_pt]):
                    start_pt -= 1
                while end_pt < len(input_ids) - 1 and self._merge_consecutive_two_token(input_ids[end_pt-1], input_ids[end_pt]):
                    end_pt += 1
                annotations.add((start_pt, end_pt, annotation[2]))
            fixed.append(annotations)
        return fixed

    def __call__(self, outputs:Dict[str, Any], encodings:Optional[List[BatchEncoding]]=None) -> Dict[str, float]:
        predictions = outputs['prediction']
        predictions = self._preprocess(predictions)
        predictions = [self.collect_spans(prediction) for prediction in predictions]

        labels = None
        if 'label' in outputs:
            labels = outputs['label']
            if labels is not None:
                labels = self._preprocess(labels)
                labels = [self.collect_spans(label) for label in labels]

        if self.tokenizer is not None and encodings is not None:
            predictions = self.fix_spans(predictions, encodings)

        metric = F1Record()
        metric_by_label = {}
        if labels is not None:
            prediction_spans = {tuple([i]+list(prediction_span)) for i, prediction_spans in enumerate(predictions) for prediction_span in prediction_spans}
            label_spans = {tuple([i]+list(label_span)) for i, label_spans in enumerate(labels) for label_span in label_spans}
            nprediction = len(prediction_spans)
            nlabel = len(label_spans)
            nmatch = len(prediction_spans.intersection(label_spans))
            # nprediction = sum([len(prediction_spans) for prediction_spans in predictions])
            # nlabel = sum([len(label_spans) for label_spans in labels])
            # nmatch = sum([len(label_spans.intersection(prediction_spans)) for prediction_spans, label_spans in zip(predictions, labels)])
            metric += np.array([nlabel, nprediction, nmatch])
            for label in self.label2id:
                lmetric = F1Record()
                ffunc = lambda t:t[3]==label
                nprediction = len(list(filter(ffunc, prediction_spans)))
                nlabel = len(list(filter(ffunc, label_spans)))
                nmatch = len(list(filter(ffunc, prediction_spans.intersection(label_spans))))
                metric_by_label[label] = [nlabel, nprediction, nmatch]

        annotations = None
        if self.save_dir is not None:
            if self.save_output:
                save_output = os.path.join(self.save_dir, "output.th")
                torch.save({'prediction': predictions, 'labels': labels, 'metric': metric, 'metric_by_label': metric_by_label}, save_output)
                print(f"save to {save_output}")
            if self.save_annotation and encodings is not None:
                annotations = self.annotate(predictions, encodings, save=True)
        if annotations is None and self.return_annotation:
            annotations = self.annotate(predictions, encodings, save=False)

        if self.return_annotation:
            return metric, metric_by_label, annotations
        else:
            return metric, metric_by_label

class WSAnnotations(object):

    def __init__(self, threshold:float, tokenizer:PreTrainedTokenizerFast, label2id:Dict[str, int], uthreshold:Optional[float]=None, id2label:Optional[Dict[int, str]]=None, save_dir:Optional[str]=None):
        self.threshold = threshold
        if uthreshold is None:
            self.uthreshold = threshold
        else:
            self.uthreshold = uthreshold
        self.tokenizer = tokenizer
        self.label2id = label2id
        if id2label is None:
            self.id2label = {v:k for k,v in label2id.items()}
            self.label2id['CND'] = len(label2id)
            self.id2label[len(label2id)] = 'CND'
        else:
            self.id2label = id2label
            self.label2id['CND'] = max(len(label2id), len(id2label))
            self.id2label[max(len(label2id), len(id2label))] = 'CND'
        self.rlabel2id = {v:k for k,v in label2id.items()}
        self.f1_tagger = F1MetricTag(
            pad_value=-100,
            ignore_labels=0,
            label2id=self.label2id,
            tokenizer=self.tokenizer,
            save_dir=save_dir,
            save_output=False,
            save_annotation=False,
            return_annotation=True)


    def collect(self, pieces, pred):
        spans = []
        span = []
        for it in range(pred.size(0)):
            if pred[it] == -100:
                if len(span) == 3:
                    spans.append(tuple(span))
                break
            if pred[it] > 0:
                if len(span) == 0:
                    if pieces[it].startswith('##'):
                        continue
                    span = [int(pred[it]), it, it+1]
                elif span[0] == pred[it]:
                    span[2] = it+1
                else:
                    if pieces[it].startswith('##'):
                        span[2] = it + 1
                    else:
                        spans.append(tuple(span))
                        span = [int(pred[it]), it, it+1]
            else:
                if len(span) == 3:
                    if pieces[it].startswith('##'):
                        span[2] = it + 1
                    else:
                        spans.append(tuple(span))
                        span = []
        return spans

    def annotate(self, input_ids:Union[torch.LongTensor, List[transformers.BatchEncoding]], outputs:Optional[torch.FloatTensor]=None, tokenizer:Optional[PreTrainedTokenizerFast]=None, return_offset:Optional[str]='char'):
        encodings = None
        if outputs is None:
            input_ids, outputs = input_ids
        if tokenizer is None:
            tokenizer = self.tokenizer
        if isinstance(input_ids, transformers.BatchEncoding):
            encodings = input_ids
            input_ids = encodings.input_ids
        elif isinstance(input_ids[0], transformers.BatchEncoding):
            encodings = input_ids
            input_ids = self.tokenizer.pad(encodings, return_tensors='pt').input_ids
        if outputs.size(1) > input_ids.size(1):
            outputs = outputs[:, :input_ids.size(1), :]

        val, pred = torch.max(outputs, dim=-1)
        mask = val > self.threshold
        umask = (val <= self.threshold) & (val > self.uthreshold)
        pred = pred + 1
        pred[~mask] = 0
        pred[umask] = self.label2id['CND']

        for idx, label in self.id2label.items():
            pred[pred==idx] = self.label2id[label]

        if tokenizer.pad_token_id is not None:
            pred[input_ids==tokenizer.pad_token_id] = -100
        if tokenizer.cls_token_id is not None:
            pred[input_ids==tokenizer.cls_token_id] = 0
        if tokenizer.sep_token_id is not None:
            pred[input_ids==tokenizer.sep_token_id] = -100

        if encodings is not None:
            metric, _, annotations = self.f1_tagger({'prediction': pred}, encodings=encodings)
            instances = [{'tokens':None, 'annotations': annotation} for annotation in annotations]
        else:
            instances = []
            for i in range(input_ids.size(0)):
                pieces = tokenizer.convert_ids_to_tokens(input_ids[i], skip_special_tokens=True)
                output = pred[i, 1:len(pieces)+1]
                span = self.collect(pieces, output)
                sentence = ''
                index = 0
                annotations = []
                for label_id, start, end in span:
                    if index >= 0 and index < start:
                        if index > 0:
                            sentence += " "
                        sentence += tokenizer.convert_tokens_to_string(pieces[index:start])
                    text = tokenizer.convert_tokens_to_string(pieces[start:end])
                    annotations.append([len(sentence)+1, len(sentence) + len(text) + 1, self.rlabel2id[label_id], text])
                    sentence += f" {text}"
                    index = end
                if index < len(pieces):
                    if index > 0:
                        sentence += " "
                    sentence += tokenizer.convert_tokens_to_string(pieces[index:])
                instances.append({'tokens': sentence, 'annotations': annotations})
        return instances
