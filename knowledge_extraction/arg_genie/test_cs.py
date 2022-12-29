import argparse 
import logging 
import os 
import random 
import timeit 
from datetime import datetime 

import torch 
from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import LearningRateMonitor, EarlyStopping, ModelCheckpoint
from pytorch_lightning.utilities.seed import seed_everything

from genie.CS_data_module import CSDataModule
from genie.model import GenIEModel 



def run_model(args):
    
    
    if not args.ckpt_name:
        d = datetime.now() 
        time_str = d.strftime('%m-%dT%H%M')
        args.ckpt_name = '{}_{}lr{}_{}'.format(args.model,  args.train_batch_size * args.accumulate_grad_batches, 
                args.learning_rate, time_str)


    args.ckpt_dir = os.path.join(f'{args.ckpt_name}')
    
    os.makedirs(args.ckpt_dir, exist_ok=True)

    checkpoint_callback = ModelCheckpoint(
        dirpath=args.ckpt_dir,
        save_top_k=2,
        monitor='val/loss',
        mode='min',
        save_weights_only=True,
        filename='{epoch}', # this cannot contain slashes 

    )

    lr_logger = LearningRateMonitor() 

    model = GenIEModel(args)
    dm = CSDataModule(args)


    if args.max_steps < 0 :
        args.max_epochs = args.min_epochs = args.num_train_epochs 
    
    

    trainer = Trainer(
        min_epochs=args.num_train_epochs,
        max_epochs=args.num_train_epochs, 
        gpus=args.gpus, 
        checkpoint_callback=checkpoint_callback, 
        accumulate_grad_batches=args.accumulate_grad_batches,
        gradient_clip_val=args.gradient_clip_val, 
        num_sanity_val_steps=0, 
        val_check_interval=0.5, # use float to check every n epochs 
        precision=16 if args.fp16 else 32,
        callbacks = [lr_logger, ],

    ) 

    if args.load_ckpt:
        model.load_state_dict(torch.load(args.load_ckpt,map_location=model.device)['state_dict']) 

    
    if args.eval_only: 
        dm.setup('test')
        trainer.test(model, datamodule=dm) #also loads training dataloader 
    else:
        dm.setup('fit')
        trainer.fit(model, dm) 
    

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Required parameters
    parser.add_argument(
        "--model", 
        type=str, 
        required=True,
        choices=['gen','pointer']
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        choices=['RAMS', 'ACE', 'ERE', 'KAIROS', 'combined']
    )
    parser.add_argument('--ontology_file', type=str, default='event_role_KAIROS_P2.json')
    parser.add_argument('--tmp_dir', type=str)
    parser.add_argument(
        "--ckpt_name",
        default=None,
        type=str,
        help="The output directory where the model checkpoints and predictions will be written.",
    )
    parser.add_argument(
        "--load_ckpt",
        default=None,
        type=str, 
    )
    parser.add_argument('--input_dir', type=str, default=None)
    parser.add_argument('--coref_dir', type=str, default='data/kairos/coref_outputs')
    parser.add_argument('--mark_trigger', action='store_true')
    parser.add_argument('--sample-gen', action='store_true', help='Do topk top-p sampling when generation.')
    parser.add_argument("--train_batch_size", default=8, type=int, help="Batch size per GPU/CPU for training.")
    parser.add_argument(
        "--eval_batch_size", default=8, type=int, help="Batch size per GPU/CPU for evaluation."
    )
    parser.add_argument(
        "--eval_only", action="store_true",
    )
    parser.add_argument("--learning_rate", default=5e-5, type=float, help="The initial learning rate for Adam.")
    parser.add_argument(
        "--accumulate_grad_batches",
        type=int,
        default=1,
        help="Number of updates steps to accumulate before performing a backward/update pass.",
    )
    parser.add_argument("--weight_decay", default=0.0, type=float, help="Weight decay if we apply some.")
    parser.add_argument("--adam_epsilon", default=1e-8, type=float, help="Epsilon for Adam optimizer.")
    parser.add_argument("--gradient_clip_val", default=1.0, type=float, help="Max gradient norm.")
    parser.add_argument(
        "--num_train_epochs", default=3, type=int, help="Total number of training epochs to perform."
    )
    parser.add_argument(
        "--max_steps",
        default=-1,
        type=int,
        help="If > 0: set total number of training steps to perform. Override num_train_epochs.",
    )
    parser.add_argument("--warmup_steps", default=0, type=int, help="Linear warmup over warmup_steps.")
    
    parser.add_argument("--gpus", default=None, help='-1 means train on all gpus')
    parser.add_argument("--seed", type=int, default=42, help="random seed for initialization")
    parser.add_argument(
        "--fp16",
        action="store_true",
        help="Whether to use 16-bit (mixed) precision (through NVIDIA apex) instead of 32-bit",
    )
    parser.add_argument("--threads", type=int, default=1, help="multiple threads for converting example to features")
    args = parser.parse_args()

    # Set seed
    seed_everything(args.seed)

    logging.debug("Training/evaluation parameters %s", args)

    run_model(args)

# /opt/conda/envs/genie/bin/python genie/convert_gen_to_cs.py \
#     --ontology_file=/arg_genie/event_role_AIDA_P2.json \
#     --gen_file=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/ru/arg_genie/ckpt/predictions.jsonl \
#     --input_dir=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/ru/pengfei \
#     --merged_file=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/ru/arg_genie/ckpt/merged.jsonl \
#     --diff_file=/shared/nas/data/m1/manling2/aida_docker_test/uiuc_ie_pipeline_fine_grained/output/output_LDC2021E11/ru/arg_genie/ckpt/diff.json
