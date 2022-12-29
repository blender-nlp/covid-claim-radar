import argparse
from dataclasses import dataclass
from typing import *
import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
import json
import os
from transformers import PreTrainedTokenizerFast, AutoTokenizer, BatchEncoding
from transformers.tokenization_utils_base import TokenSpan

Entailment = Tuple[str, str]

@dataclass
class Instance(object):
    tokens : Union[List[str], str]
    annotations : List[Tuple[int, int, str]]
    sentence_id : str
    links : Optional[List[List[List]]] = None

    @classmethod
    def from_oneie(cls, oneie):
        if 'sentence' in oneie:
            tokens = oneie['sentence']
        else:
            tokens = oneie['tokens']
        annotations = []
        for event in oneie['event_mentions']:
            start = event['trigger']['start']
            end = event['trigger']['end']
            label = event['event_type']
            annotations.append((start, end, label))
        sentence_id = oneie["sent_id"]
        return cls(tokens=tokens, annotations=annotations, sentence_id=sentence_id)

def _to_instance(data, sentence_id_prefix:Optional[str]=None):
    if sentence_id_prefix is None:
        sentence_id_prefix = ""
    elif not sentence_id_prefix.endswith("_"):
        sentence_id_prefix += "_"
    if 'annotations' in data[0]:
        if 'sentence_id' in data[0]:
            for t in data:
                t["sentence_id"] = f"{sentence_id_prefix}{t['sentence_id']}"
            return [Instance(**t) for t in data]
        else:
            return [Instance(**t, sentence_id=f"{sentence_id_prefix}{i}") for i, t in enumerate(data)]
    else:
        return [Instance.from_oneie(t) for t in data]

class IDataset(Dataset):
    _DEFAULT_SETTING = "token"
    _SEED = 2147483647
    def __init__(self,
        instances:List[Instance],
        label2id:Dict[str, int],
        tokenizer:PreTrainedTokenizerFast,
        setting:Optional[str]=None,
        max_length:Optional[int]=None,
        mask_prob:Optional[float]=None,
        label_templates:Optional[Dict[str, str]]=None,
        examples:Optional[List[Instance]]=None,
        short_epoch:Optional[bool]=None,
        seed:Optional[int]=None,
        nearest_examples:Optional[Dict[str, List[int]]]=None,
        label_ignore:Optional[Union[List, Set, int]]=None,
        *args,
        **kwargs) -> None:
        super().__init__()
        if isinstance(label_ignore, int):
            label_ignore = {label_ignore}
        elif isinstance(label_ignore, list):
            label_ignore = set(label_ignore)
        self.label_ignore = set() if label_ignore is None else label_ignore
        self.label_ignore = {label for label in label2id if label2id[label] in {1,2,3,4,5,6,7,12,14,15}}
        self.label2id = label2id
        self.label_offset = 1 if "NA" in self.label2id else 0
        self.instances = instances
        self.instance_tokenized = isinstance(instances[0].tokens, list)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.mask_prob = mask_prob
        self.short_epoch = short_epoch
        self._index_map = None
        self._sent_labels = None
        self._times = 8
        if self.short_epoch:
            total_length = sum(len(t.annotations) for t in instances)
            self._index_map = []
            self._sent_labels = []
            for isent, sent in enumerate(instances):
                sent_labels = []
                for a in sent.annotations:
                    self._index_map.append((isent, self.label2id[a[2]]-1))
                    sent_labels.append(self.label2id[a[2]]-1)
                self._sent_labels.append(sent_labels)
                _times = self._times
                self._index_map.extend([(isent, -1)] * (_times-len(sent_labels)))
        if setting is None:
            self.setting = self._DEFAULT_SETTING
        else:
            self.setting = setting
        self.entailment = None
        if label_templates is not None:
            self.entailment = [None for _ in range(len(label_templates))]
            for label in self.label2id:
                if self.label2id[label] > self.label_offset - 1:
                    self.entailment[self.label2id[label]-1] = (label, label_templates[label])
        self.examples = examples
        self.nearest_examples = nearest_examples
        if seed is None:
            seed = self._SEED
        else:
            seed = seed
        self._generator = np.random.default_rng(seed)

    def __len__(self) -> int:
        if self.setting == "nli":
            if self.short_epoch:
                return len(self.instances)#len(self._index_map)
            else:
                return len(self.instances) * len(self.entailment)
        else:
            return len(self.instances)

    def __getitem__(self, index: int) -> Union[Instance, Tuple[Instance, Entailment]]:
        if self.setting == "nli":
            if self.short_epoch:
                # index_sentence, index_entailment = self._index_map[index]
                # if index_entailment == -1:
                #     negative_labels = [i for i in range(len(self.entailment)) if i not in self._sent_labels[index_sentence]]
                #     index_entailment = self._generator.choice(negative_labels)
                negative_labels = [i for i in range(len(self.entailment)) if i not in self._sent_labels[index]]
                index_entailment = self._generator.choice(negative_labels, self._times - len(self._sent_labels[index]))
                instance = [(self.instances[index], self.entailment[i]) for i in self._sent_labels[index]] + \
                    [(self.instances[index], self.entailment[i]) for i in index_entailment]
                return instance
            else:
                index_sentence = index // len(self.entailment)
                index_entailment = index % len(self.entailment)
                instance = (self.instances[index_sentence], self.entailment[index_entailment])
                return instance
        else:
            return self.instances[index]

    def sample_random_examples(self, nsample:int, is_nli:Optional[bool]=None):
        if self.examples is None:
            return None
        else:
            if is_nli:
                index_example = self._generator.choice(len(self.examples),  nsample // self._times)
                examples = [self.examples[i] for i in index_example]
                instances = []
                for example in examples:
                    _labels = list(range(len(self.entailment)))
                    for ann in example.annotations:
                        instances.append((example, self.entailment[self.label2id[ann[2]]-1]))
                        _labels[self.label2id[ann[2]]-1] = -1
                    _labels = [t for t in _labels if t > 0]
                    instances.extend([
                        (example, self.entailment[i]) for i in self._generator.choice(_labels, self._times - len(self.entailment) + len(_labels))
                    ])
                return instances
            else:
                return [self.examples[i] for i in self._generator.choice(len(self.examples), nsample)]

    def sample_nearest_examples(self, sentence_ids:List[str], labels:Optional[List[str]]=None):
        if self.nearest_examples is None or self.examples is None:
            return None
        nsamples = len(sentence_ids)
        kept_ids = [i for i, sid in enumerate(sentence_ids) if sid in self.nearest_examples]
        if len(kept_ids) == 0:
            return None
        else:
            sentence_ids = [sentence_ids[i] for i in kept_ids]
            if labels is not None:
                labels = [labels[i] for i in kept_ids]
        selected = None
        if labels is None:
            selected = [
                self.examples[self.nearest_examples[sid][self._generator.randint(len(self.nearest_examples[sid]))]]
                for sid in sentence_ids
            ]
            if len(selected) < nsamples:
                additional = self._generator.choice(len(self.examples), nsamples - len(selected))
                selected.extend([self.examples[i] for i in additional])
        else:
            selected = [
                (
                    self.examples[self.nearest_examples[sid][self._generator.randint(len(self.nearest_examples[sid]))]],
                    self.entailment[self.label2id[label]-1]
                ) for sid, label in zip(sentence_ids, labels)
            ]
            if len(selected) < nsamples:
                additional = self._generator.choice(len(self.examples), nsamples - len(selected))
                additional_entailment = self._generator.choice(len(self.entailment), nsamples, replace=True)
                selected.extend([(self.examples[i], self.entailment[j]) for i,j in zip(additional, additional_entailment)])
        if len(selected) > nsamples:
            selected_idx = self._generator.choice(len(selected), nsamples)
            selected = [selected[i] for i in selected_idx]
        return selected


    def collate_batch(self, batch:List[Union[Instance, Tuple[Instance, Entailment]]]) -> BatchEncoding:
        # if self.short_epoch:
        #     batch = [tt for t in batch for tt in t]
        is_nli = not isinstance(batch[0], Instance)
        text = None
        labels = None
        spans = None
        if is_nli:
            text = [i[0].tokens + " </s></s> " + i[1][1] for i in batch]
            labels = torch.LongTensor([i[1][0] in [t[2] for t in i[0].annotations] for i in batch])
        else:
            text = [i.tokens for i in batch]
        encoded:BatchEncoding = self.tokenizer(
            text=text,
            max_length=self.max_length,
            is_split_into_words=self.instance_tokenized,
            add_special_tokens=True,
            padding=True,
            truncation=True,
            return_attention_mask=True,
            return_special_tokens_mask=True,
            return_tensors='pt'
        )
        special_token_mask = encoded.pop("special_tokens_mask")
        need_mask = is_nli and self.mask_prob is not None and self.mask_prob > 0


        if not is_nli or need_mask:
            if is_nli:
                annotations = [i[0].annotations for i in batch]
            else:
                annotations = [i.annotations for i in batch]
            if self.setting == "span":
                _n_annotations = max(len(t) for t in annotations)
                spans = torch.zeros(len(batch), _n_annotations, encoded.input_ids.size(1), dtype=torch.float)
                labels = torch.empty(len(batch), _n_annotations, dtype=torch.long).fill_(-100)
            elif self.setting == "token":
                labels = torch.zeros_like(encoded.input_ids, dtype=torch.long)
            elif self.setting == "sentence":
                labels = torch.zeros(len(batch), len(self.label2id) - self.label_offset, dtype=torch.float)
            elif self.setting == "nli":
                spans = torch.zeros_like(encoded.input_ids, dtype=torch.bool)
            for ibatch, anns in enumerate(annotations):
                for iann, ann in enumerate(anns):
                    start, end, label = ann[:3]
                    label_id = self.label2id[label] if label not in self.label_ignore else 0
                    if self.setting == "sentence":
                        if label_id >= self.label_offset:
                            labels[ibatch, label_id - self.label_offset] = 1
                    else:
                        if self.instance_tokenized:
                            tok_start = encoded.word_to_tokens(ibatch, start)
                            tok_end = encoded.word_to_tokens(ibatch, end)
                        else:
                            tok_start = encoded.char_to_token(ibatch, start)
                            tok_end = encoded.char_to_token(ibatch, end-1)
                        if tok_end is not None:
                            if isinstance(tok_start, TokenSpan):
                                tok_start = tok_start.start
                            if isinstance(tok_end, TokenSpan):
                                tok_end = tok_end.start
                            else:
                                tok_end += 1
                            if self.setting == "span":
                                spans[ibatch, iann, tok_start:tok_end] = 1. / (tok_end - tok_start)
                                labels[ibatch, iann] = label_id
                            elif self.setting == "token":
                                labels[ibatch, tok_start:tok_end] = label_id
                            elif self.setting == "nli":
                                if label == batch[ibatch][1][0]:
                                    spans[ibatch, tok_start:tok_end] = 1

        if need_mask:
            probability_matrix = torch.full(encoded.input_ids.size(), self.mask_prob)
            probability_matrix.masked_fill_(special_token_mask, value=0.0)
            masked_indices = torch.bernoulli(probability_matrix).bool()
            encoded.input_ids[masked_indices] = self.tokenizer.convert_tokens_to_ids(self.tokenizer.mask_token)
            zero_label_indices = torch.any(masked_indices * spans, dim=1)
            labels[zero_label_indices] = 0
            spans = None

        encoded["labels"] = labels
        encoded["spans"] = spans
        return encoded

    def collate_fn(self, batch:List[Union[Instance, Tuple[Instance, Entailment]]]) -> BatchEncoding:
        if self.short_epoch:
            batch = [tt for t in batch for tt in t]
        is_nli = not isinstance(batch[0], Instance)
        sentence_ids = None
        sentence_labels = None
        if is_nli:
            sentence_labels = [t[1][0] for t in batch]
            sentence_ids = [t[0].sentence_id for t in batch]
        else:
            sentence_ids = [t.sentence_id for t in batch]
        input_batch = self.collate_batch(batch)

        examples = self.sample_random_examples(len(batch), is_nli)

        if examples is not None:
            ref_batch = self.collate_batch(examples)
            for k, v in ref_batch.items():
                input_batch[f"ref_{k}"] = v

        remove_keys = [key for key in input_batch if input_batch[key] is None]
        for key in remove_keys:
            input_batch.pop(key)
        return input_batch

def get_example_dataset(
    opts:Optional[argparse.Namespace]=None,
    root:Optional[str]=None,
    dataset:Optional[str]=None,
    model_name:Optional[str]=None,
    setting:Optional[str]=None,
    max_length:Optional[int]=None):
    if opts is not None:
        root = getattr(opts, "root", None) if root is None else root
        dataset = getattr(opts, "dataset", None) if dataset is None else dataset
        setting = getattr(opts, "setting", None) if setting is None else setting
        model_name = getattr(opts, "model_name", None) if model_name is None else model_name
        max_length = getattr(opts, "max_length", None) if max_length is None else max_length
    example_file = os.path.join(root, f"{dataset}.example.char.jsonl")
    label_info_file = os.path.join(root, "label_info.json")
    print("loading files...")
    with open(label_info_file, "rt") as f:
        label_info = json.load(f)
        label2id = {label: info["id"] for label, info in label_info.items()}; label2id["NA"] = 0
        label_templates = {label: info["template"][0].replace("<", "").replace(">", "") for label, info in label_info.items()}
    with open(example_file, "rt") as fp:
        examples = json.load(fp)
        for example in examples:
            example['annotations'] = [[x, y, z.split(".")[1] if z.startswith("CND") else z] for x,y,z in example['annotations']]
            example['sentence_id'] = f"example_{example['sentence_id']}"
        examples = _to_instance(examples, "example")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    dataset = IDataset(
        instances=examples,
        label2id=label2id,
        tokenizer=tokenizer,
        setting=setting,
        short_epoch=setting == "nli",
        max_length=max_length,
        mask_prob=None,
        label_templates=label_templates)
    return dataset

def get_dev_test_encodings(
    opts:Optional[argparse.Namespace]=None,
    root:Optional[str]=None,
    dataset:Optional[str]=None,
    model_name:Optional[str]=None,
    setting:Optional[str]=None,
    max_length:Optional[int]=None,
    weak_corpus:Optional[bool]=None,
    weak_annotation:Optional[Tuple[str,str]]=None,
    test_only:Optional[bool]=None,
    seed:Optional[int]=None,
    *args,
    **kwargs):

    if opts is not None:
        root = getattr(opts, "root", None) if root is None else root
        dataset = getattr(opts, "dataset", None) if dataset is None else dataset
        model_name = getattr(opts, "model_name", None) if model_name is None else model_name
        setting = getattr(opts, "setting", None) if setting is None else setting
        max_length = getattr(opts, "max_length", None) if max_length is None else max_length
        weak_corpus = getattr(opts, "weak_corpus", None) if weak_corpus is None else weak_corpus
        weak_annotation = getattr(opts, "weak_annotation", None) if weak_annotation is None else weak_annotation
        test_only = getattr(opts, "test_only", None) if test_only is None else test_only
        seed = getattr(opts, "seed", None) if seed is None else seed
    weakly_supervised = weak_corpus != "none"
    weak_dataset = (weak_corpus, weak_annotation)
    if setting == "span":
        train_file = os.path.join(root, f"{dataset}.train.span.jsonl")
        dev_file = os.path.join(root, f"{dataset}.dev.span.jsonl")
        test_file = os.path.join(root, f"{dataset}.test.span.jsonl")
    else:
        train_file = os.path.join(root, f"{dataset}.train.char.jsonl")
        if not os.path.exists(train_file):
            train_file = os.path.join(root, f"{dataset}.train.jsonl")
        dev_file = os.path.join(root, f"{dataset}.dev.char.jsonl")
        if not os.path.exists(dev_file):
            dev_file = os.path.join(root, f"{dataset}.dev.jsonl")
        test_file = os.path.join(root, f"{dataset}.test.char.jsonl")
        if not os.path.exists(test_file):
            test_file = os.path.join(root, f"{dataset}.test.jsonl")
    weakly_supervised_data_file = os.path.join(root, weak_dataset[0], f"weakly_supervised_data_{weak_dataset[1]}.jsonl")
    weakly_supervised_dev_file = os.path.join(root, weak_dataset[0], f"weakly_supervised_dev_{weak_dataset[1]}.jsonl")
    load_weakly_file = weakly_supervised and not test_only
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if load_weakly_file:
        with open(weakly_supervised_dev_file, "rt") as fp:
            dev_weak = _to_instance([json.loads(line) for line in fp])
        dev_weak = [tokenizer(
                text=t.tokens,
                max_length=max_length,
                is_split_into_words=isinstance(t.tokens, list),
                add_special_tokens=True,
                padding=True,
                truncation=True) for t in dev_weak]
    else:
        dev_weak = None
    with open(dev_file, "rt") as f:
        dev = _to_instance([json.loads(line) for line in f], "dev")
    with open(test_file, "rt") as f:
        test = _to_instance([json.loads(line) for line in f], "test")
    dev = [tokenizer(
            text=t.tokens,
            max_length=max_length,
            is_split_into_words=isinstance(t.tokens, list),
            add_special_tokens=True,
            padding=True,
            truncation=True) for t in dev]
    test = [tokenizer(
            text=t.tokens,
            max_length=max_length,
            is_split_into_words=isinstance(t.tokens, list),
            add_special_tokens=True,
            padding=True,
            truncation=True) for t in test]
    return dev_weak, dev, test

def get_dataset(
    opts:Optional[argparse.Namespace]=None,
    root:Optional[str]=None,
    dataset:Optional[str]=None,
    model_name:Optional[str]=None,
    setting:Optional[str]=None,
    max_length:Optional[int]=None,
    weak_corpus:Optional[bool]=None,
    weak_annotation:Optional[Tuple[str,str]]=None,
    example_regularization:Optional[bool]=None,
    example_training:Optional[bool]=None,
    example_validation:Optional[bool]=None,
    example_ratio:Optional[float]=None,
    short_epoch:Optional[bool]=None,
    test_only:Optional[bool]=None,
    seed:Optional[int]=None,
    *args,
    **kwargs) -> Tuple[Union[IDataset, None], Union[IDataset, None], IDataset]:

    if opts is not None:
        root = getattr(opts, "root", None) if root is None else root
        dataset = getattr(opts, "dataset", None) if dataset is None else dataset
        model_name = getattr(opts, "model_name", None) if model_name is None else model_name
        setting = getattr(opts, "setting", None) if setting is None else setting
        max_length = getattr(opts, "max_length", None) if max_length is None else max_length
        weak_corpus = getattr(opts, "weak_corpus", None) if weak_corpus is None else weak_corpus
        weak_annotation = getattr(opts, "weak_annotation", None) if weak_annotation is None else weak_annotation
        example_training = getattr(opts, "example_training", None) if example_training is None else example_training
        example_validation = getattr(opts, "example_validation", None) if example_validation is None else example_validation
        example_regularization = getattr(opts, "example_regularization", None) if example_regularization is None else example_regularization
        example_ratio = getattr(opts, "example_ratio", None) if example_ratio is None else example_ratio
        short_epoch = getattr(opts, "short_epoch", None) if short_epoch is None else short_epoch
        test_only = getattr(opts, "test_only", None) if test_only is None else test_only
        seed = getattr(opts, "seed", None) if seed is None else seed
    weakly_supervised = weak_corpus != "none"
    weak_dataset = (weak_corpus, weak_annotation)

    example_file = os.path.join(root, f"{dataset}.example.char.jsonl")
    label_info_file = os.path.join(root, "label_info.json")
    if setting == "span":
        train_file = os.path.join(root, f"{dataset}.train.span.jsonl")
        dev_file = os.path.join(root, f"{dataset}.dev.span.jsonl")
        test_file = os.path.join(root, f"{dataset}.test.span.jsonl")
    else:
        train_file = os.path.join(root, f"{dataset}.train.char.jsonl")
        if not os.path.exists(train_file):
            train_file = os.path.join(root, f"{dataset}.train.jsonl")
        dev_file = os.path.join(root, f"{dataset}.dev.char.jsonl")
        if not os.path.exists(dev_file):
            dev_file = os.path.join(root, f"{dataset}.dev.jsonl")
        test_file = os.path.join(root, f"{dataset}.test.char.jsonl")
        if not os.path.exists(test_file):
            test_file = os.path.join(root, f"{dataset}.test.jsonl")
    if setting == "span":
        weakly_supervised_data_file = os.path.join(root, weak_dataset[0], f"weakly_supervised_data_{weak_dataset[1]}.span.jsonl")
    else:
        weakly_supervised_data_file = os.path.join(root, weak_dataset[0], f"weakly_supervised_data_{weak_dataset[1]}.jsonl")
    weakly_supervised_dev_file = os.path.join(root, weak_dataset[0], f"weakly_supervised_dev_{weak_dataset[1]}.jsonl")
    nearest_example_file = os.path.join(root, weak_dataset[0], f"train_data_nearest_examples.json")

    load_example_data = example_regularization or example_training or example_validation
    load_nearest_data = False and example_regularization and weakly_supervised
    load_train_dev_file = not weakly_supervised and not test_only
    load_weakly_file = weakly_supervised and not test_only
    load_label_template = setting == "nli"

    split_nearest_data = False and example_regularization and weakly_supervised
    add_example_to_train = example_training and not example_regularization
    add_example_to_dev = example_validation and not example_training and not example_validation

    build_train_dev_dataset = not test_only

    label_info = label2id = None
    examples = None
    nearest_examples = None
    train = dev = test = dev_weak = None
    train_nearest = None
    label_templates = None

    train_dataset = None
    dev_dataset = None
    dev_weak_dataset = None

    print("loading files...")
    with open(label_info_file, "rt") as f:
        label_info = json.load(f)
        label2id = {label: info["id"] for label, info in label_info.items()}; label2id["NA"] = 0
        if load_label_template:
            label_templates = {label: info["template"][0].replace("<", "").replace(">", "") for label, info in label_info.items()}
    if load_example_data:
        with open(example_file, "rt") as fp:
            examples = json.load(fp)
            for example in examples:
                example['annotations'] = [[x, y, z.split(".")[1] if z.startswith("CND") else z] for x,y,z in example['annotations']]
                example['sentence_id'] = f"example_{example['sentence_id']}"
            examples = _to_instance(examples, "example")
    if load_nearest_data:
        with open(nearest_example_file) as fp:
            nearest_examples = json.load(fp)
    if load_train_dev_file:
        with open(train_file, "rt") as f:
            train = _to_instance([json.loads(line) for line in f], "train")
        with open(dev_file, "rt") as f:
            dev = _to_instance([json.loads(line) for line in f], "dev")
    if load_weakly_file:
        with open(weakly_supervised_data_file, "rt") as fp:
            train = _to_instance([json.loads(line) for line in fp])
            train = [t for t in train if len(t.annotations) > 0]
        with open(weakly_supervised_dev_file, "rt") as fp:
            dev_weak = _to_instance([json.loads(line) for line in fp])
        with open(dev_file, "rt") as f:
            dev = _to_instance([json.loads(line) for line in f], "dev")
    with open(test_file, "rt") as f:
        test = _to_instance([json.loads(line) for line in f], "test")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    print("processing files...")
    if train is not None and len(train) < 19216 // 2:
        train = train * (19216 // len(train))

    if split_nearest_data:
        train_nearest = dict(zip([t.sentence_id for t in train], nearest_examples))
    if add_example_to_train:
        if example_ratio > 2:
            train = examples * (len(train) // len(examples))
        elif example_ratio > 0:
            train = train + examples * (len(train) // len(examples))
        else:
            train = train + examples

    if add_example_to_dev:
        dev = dev + example

    print("building pytorch datasets...")
    if build_train_dev_dataset:
        train_dataset = IDataset(
            instances=train,
            label2id=label2id,
            tokenizer=tokenizer,
            setting=setting,
            short_epoch=setting == "nli",
            max_length=max_length,
            examples=examples,
            mask_prob=None,
            seed=seed,
            nearest_examples=train_nearest,
            label_templates=label_templates)
        dev_dataset = IDataset(
            instances=dev,
            label2id=label2id,
            tokenizer=tokenizer,
            setting=setting,
            max_length=max_length,
            label_templates=label_templates)
        if dev_weak is not None:
            dev_weak_dataset = IDataset(
                instances=dev_weak,
                label2id=label2id,
                tokenizer=tokenizer,
                setting=setting,
                max_length=max_length,
                label_templates=label_templates)
    test_dataset = IDataset(
        instances=test,
        label2id=label2id,
        tokenizer=tokenizer,
        setting=setting,
        max_length=max_length,
        label_templates=label_templates)

    if dev_weak_dataset is None:
        return train_dataset, dev_dataset, test_dataset
    else:
        return train_dataset, dev_weak_dataset, dev_dataset, test_dataset

def get_data(
    opts:Optional[argparse.Namespace]=None,
    batch_size:Optional[int]=None,
    eval_batch_size:Optional[int]=None,
    num_workers:Optional[int]=None,
    seed:Optional[int]=None,
    root:Optional[str]=None,
    dataset:Optional[str]=None,
    model_name:Optional[str]=None,
    setting:Optional[str]=None,
    max_length:Optional[int]=None,
    weak_corpus:Optional[bool]=None,
    weak_annotation:Optional[Tuple[str,str]]=None,
    example_regularization:Optional[bool]=None,
    example_training:Optional[bool]=None,
    example_validation:Optional[bool]=None,
    example_ratio:Optional[float]=None,
    test_only:Optional[bool]=None,
    shuffle:Optional[bool]=None,
    *args,
    **kwargs):
    _default_num_workers = 0
    _default_seed = 44739242
    if opts is not None:
        root = getattr(opts, "root", None) if root is None else root
        dataset = getattr(opts, "dataset", None) if dataset is None else dataset
        batch_size = getattr(opts, "batch_size", None) if batch_size is None else batch_size
        eval_batch_size = getattr(opts, "eval_batch_size", batch_size) if eval_batch_size is None else eval_batch_size
        num_workers = getattr(opts, "num_workers", _default_num_workers) if num_workers is None else num_workers
        seed = getattr(opts, "seed", _default_seed) if seed is None else seed
        model_name = getattr(opts, "model_name", None) if model_name is None else model_name
        setting = getattr(opts, "setting", None) if setting is None else setting
        max_length = getattr(opts, "max_length", None) if max_length is None else max_length
        weak_corpus = getattr(opts, "weak_corpus", None) if weak_corpus is None else weak_corpus
        weak_annotation = getattr(opts, "weak_annotation", None) if weak_annotation is None else weak_annotation
        example_training = getattr(opts, "example_training", None) if example_training is None else example_training
        example_validation = getattr(opts, "example_validation", None) if example_validation is None else example_validation
        example_regularization = getattr(opts, "example_regularization", None) if example_regularization is None else example_regularization
        example_ratio = getattr(opts, "example_ratio", None) if example_ratio is None else example_ratio
        test_only = getattr(opts, "test_only", None) if test_only is None else test_only
    if shuffle is None:
        shuffle = True
    weakly_supervised = weak_corpus != "none"
    weak_dataset = (weak_corpus, weak_annotation)

    with open(os.path.join(root, "label_info.json"), "rt") as f:
        label_info = json.load(f)
        label2id = {label: info["id"] for label, info in label_info.items()}; label2id["NA"] = 0

    datasets = get_dataset(
        root=root,
        dataset=dataset,
        model_name=model_name,
        setting=setting,
        max_length=max_length,
        weak_corpus=weak_corpus,
        weak_annotation=weak_annotation,
        example_regularization=example_regularization,
        example_training=example_training,
        example_validation=example_validation,
        example_ratio=example_ratio,
        seed=seed,
        test_only=test_only)

    if test_only:
        loaders = [None] * (len(datasets) - 1)
    else:
        loaders = []
        loaders.append(DataLoader(
            dataset=datasets[0],
            batch_size=batch_size,
            shuffle=shuffle,
            drop_last=False,
            collate_fn=datasets[0].collate_fn,
            pin_memory=True,
            num_workers=num_workers,
            generator=torch.Generator().manual_seed(seed)
        ))
        loaders.extend([DataLoader(
            dataset=d,
            batch_size=batch_size if eval_batch_size <= 0 else eval_batch_size,
            shuffle=False,
            drop_last=False,
            collate_fn=d.collate_fn,
            pin_memory=True,
            num_workers=num_workers) for d in datasets[1:-1]])
    test_loader = DataLoader(
        dataset=datasets[-1],
        batch_size=batch_size if eval_batch_size <= 0 else eval_batch_size,
        shuffle=False,
        drop_last=False,
        collate_fn=datasets[-1].collate_fn,
        pin_memory=True,
        num_workers=num_workers)
    loaders.append(test_loader)
    return loaders, label2id

def construct_inputs_for_trigger_detection(
    candidates:Union[List[Instance], str],
    sentence_predictions:List[List[str]],
    templates:Dict[str, str],
    mask_token:Optional[str]=None,
    tokenizer:Optional[PreTrainedTokenizerFast]=None,
    batch_size:Optional[int]=None,
    max_length:Optional[int]=None,
    return_dataset:bool=False,
    return_dataloader:bool=False):
    if tokenizer is not None:
        mask_token = getattr(tokenizer, "mask_token", mask_token)
    if mask_token is None:
        raise ValueError("must provide mask token to contruct inputs")
    if tokenizer is None and (return_dataset or return_dataloader):
        raise ValueError("must provide tokenizer if return dataset or return dataloader")

    if isinstance(candidates, str):
        with open(candidates, "rt") as fread:
            candidates = _to_instance([json.loads(t) for t in fread])

    inputs = []
    labels = []
    boundaries = []
    for candidate_sent, sent_pred in zip(candidates, sentence_predictions):
        if len(sent_pred) == 0:
            continue
        for pred in sent_pred:
            for candidate_ann in candidate_sent.annotations:
                start = candidate_ann[0]
                end = candidate_ann[1]
                label = candidate_ann[2]
                if " " in candidate_ann[3]:
                    continue
                input_sent = candidate_sent.tokens[:start] + mask_token + candidate_sent.tokens[end:]
                inputs.append(f"{input_sent} </s></s> {templates[pred]}")
                labels.append(int(label!=pred))
            boundaries.append(len(inputs))

    class _Dataset(Dataset):
        def __init__(self, inputs:List[str], labels:List[int], tokenizer:PreTrainedTokenizerFast):
            self.inputs = inputs
            self.labels = labels
            self.tokenizer = tokenizer
        def __len__(self):
            return len(self.inputs)
        def __getitem__(self, index) -> Tuple[str, int]:
            return (self.inputs[index], self.labels[index])
        def collate_fn(self, batch:List[Tuple[str, int]]):
            inputs = [t[0] for t in batch]
            labels = torch.LongTensor([t[1] for t in batch])

            encoded:BatchEncoding = self.tokenizer(
                text=inputs,
                max_length=max_length,
                is_split_into_words=False,
                add_special_tokens=True,
                padding=True,
                truncation=True,
                return_attention_mask=True,
                return_tensors='pt'
            )
            encoded["labels"] = labels
            return encoded

    output = (inputs, labels)
    output_dataset = None
    output_loader = None
    if return_dataset or return_dataloader:
        output_dataset = _Dataset(*output, tokenizer)
    if return_dataloader:
        output_loader = DataLoader(
            dataset=output_dataset,
            batch_size=batch_size if batch_size else 32,
            shuffle=False,
            drop_last=False,
            collate_fn=output.collate_fn,
            pin_memory=True,
            num_workers=0
        )

    if not (return_dataset or return_dataloader):
        return output, boundaries
    elif return_dataset and (not return_dataloader):
        return output_dataset, boundaries
    elif (not return_dataset) and return_dataloader:
        return output_loader, boundaries
    else:
        return output_dataset, output_loader, boundaries
