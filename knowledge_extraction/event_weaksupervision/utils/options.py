import argparse
import importlib
import os
import glob
from utils.default_options import define_default_arguments


def define_arguments(parser):
    parser.add_argument('--root', type=str, default="", help="")
    parser.add_argument('--batch-size', type=int, default=8, help="")
    parser.add_argument('--eval-batch-size', type=int, default=32, help="")
    parser.add_argument('--patience', type=int, default=3, help="")
    parser.add_argument('--hidden-dim', type=int, default=512, help="")
    parser.add_argument('--max-length', type=int, default=96, help="")
    parser.add_argument('--run-fold', type=int, default=0, help="")
    parser.add_argument('--accumulation-steps', type=int, default=1, help="")
    parser.add_argument('--no-gpu', action="store_true", help="don't use gpu")
    parser.add_argument('--example-regularization', action="store_true", help="")
    parser.add_argument('--example-training', action="store_true", help="")
    parser.add_argument('--example-ratio', type=float, default=1., help="")
    parser.add_argument('--example-validation', action="store_true", help="")
    parser.add_argument('--dataset', choices=['ace', "ere"], default='ace', help="")
    parser.add_argument('--weak-corpus', choices=["ace", "ere", "none"], default='ace', help="")
    parser.add_argument('--weak-annotation', choices=['kw', "label", "cluster"], default='label', help="")
    parser.add_argument('--gpu', type=str, default='0', help="gpu")
    parser.add_argument('--max-grad-norm', type=float, default=1, help="")
    parser.add_argument('--learning-rate', type=float, default=1e-5, help="")
    parser.add_argument('--decay', type=float, default=1e-2, help="")
    parser.add_argument('--warmup-step', type=float, default=1200, help="")
    parser.add_argument('--seed', type=int, default=44739242, help="random seed")
    parser.add_argument('--log-dir', type=str, default="./log/", help="path to save log file")
    parser.add_argument('--save-model', type=str, default="model", help="prefix to save checkpoints")
    parser.add_argument('--model-name', type=str, default="bert-large-cased", help="pretrained lm name")
    parser.add_argument('--load-model', type=str, default="", help="path to saved checkpoint")
    parser.add_argument('--train-epoch', type=int, default=25, help='epochs to train')
    parser.add_argument('--train-step', type=int, default=-1, help='steps to train')
    parser.add_argument('--test-only', action="store_true", help='is testing')
    parser.add_argument('--continue-train', action="store_true", help='is testing')
    parser.add_argument('--clean-log-dir', action="store_true", help='is testing')
    parser.add_argument('--setting', choices=['token', "span", "nli", "sentence"], default="token")


def define_arguments_for_weak_supervision(parser):
    parser.add_argument("--train-file", "-tr", type=str, default="")
    parser.add_argument("--dev-file", "-de", type=str, default="")
    parser.add_argument("--preprocess_func", "-f", type=str, default="")
    parser.add_argument("--corpus-jsonl", "-cj", type=str, default="")
    parser.add_argument("--example-json", "-ej", type=str, default="")
    parser.add_argument("--evaluation-json", "-eval", type=str, default="")
    parser.add_argument("--threshold", "-th", type=float, default=-1)
    parser.add_argument("--label-json", "-lj", type=str, default="")
    parser.add_argument("--model-name", "-mn", type=str, default="bert-large-cased")
    parser.add_argument("--encoding-save-dir", "-ed", type=str, default="")
    parser.add_argument("--output-save-dir", "-kd", type=str, default="")
    parser.add_argument("--evaluate", "-e", action="store_true")
    parser.add_argument("--force", action="store_true")


def parse_arguments():
    parser = argparse.ArgumentParser()
    cwd = os.getcwd()
    path = "default_options" if cwd.endswith("utils") else "utils.default_options"
    default_options = importlib.util.find_spec(path)
    if default_options: 
        define_default_arguments = default_options.loader.load_module().define_default_arguments
        define_default_arguments(parser)
    else:
        define_arguments(parser)
    args = parser.parse_args()
    args.log = os.path.join(args.log_dir, f"logfile.log.{args.run_fold}")
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir)
    if args.clean_log_dir and (not args.test_only) and (not args.continue_train) and os.path.exists(args.log_dir):
        existing_logs = glob.glob(os.path.join(args.log_dir, "*"))
        for _t in existing_logs:
            os.remove(_t)
    if args.setting == "nli":
        args.model_name = "roberta-large-mnli"
    return args


def parse_arguments_for_weak_supervision():
    parser = argparse.ArgumentParser()
    cwd = os.getcwd()
    path = "default_options" if cwd.endswith("utils") else "utils.default_options"
    default_options = importlib.util.find_spec(path)
    if default_options: 
        define_default_arguments_for_weak_supervision = default_options.loader.load_module().define_default_arguments_for_weak_supervision
        define_default_arguments_for_weak_supervision(parser)
    else:
        define_arguments_for_weak_supervision(parser)
    args = parser.parse_args()
    return args