import warnings
import torch
import os
import logging
import datetime
import numpy as np
import torch
from tqdm import tqdm
from typing import *
from .utils import F1Record, Record


class Worker(object):

    def __init__(self, opts):
        super().__init__()
        self.train_epoch = opts.train_epoch
        self.no_gpu = opts.no_gpu
        self.gpu = opts.gpu
        self.distributed = self.gpu.count(",") > 0
        self.save_model = opts.save_model
        self.load_model = opts.load_model
        self.log = opts.log
        log_dirs = os.path.split(self.log)[0]
        if not os.path.exists(log_dirs):
            os.makedirs(log_dirs)
        self.log_dir = log_dirs
        logging.basicConfig(filename=self.log, level=logging.INFO)
        self._log = logging.info
        self.epoch = 0
        self.optimization_step = 0
        self.epoch_outputs = dict()
        metric = getattr(opts, 'metric', 'f1')
        if metric == 'f1':
            self.metric = F1Record
        else:
            self.metric = Record
        accumulation_steps = getattr(opts, 'accumulation_steps', 1)
        self.accumulation_step = accumulation_steps
        self.accumulation_pool = []
        self.max_grad_norm = opts.max_grad_norm
        self.train_iterator = None
        self.train_last_it = -1

    @classmethod
    def from_options(cls, train_epoch:int, no_gpu:bool, gpu:int, save_model:str, load_model:str, log:str):
        class Opts:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        opts = Opts(
            train_epoch = train_epoch,
            no_gpu = no_gpu,
            gpu = gpu,
            save_model = save_model,
            load_model = load_model,
            log = log)
        return cls(opts)

    @classmethod
    def _to_device(cls, instance:Union[torch.Tensor,List[torch.Tensor],Tuple[torch.Tensor,...],Dict[Any,torch.Tensor]], device:Union[torch.device, None]=None):
        if isinstance(instance, list):
            return [cls._to_device(t, device) for t in instance]
        elif isinstance(instance, dict):
            return {key: cls._to_device(value, device=device) for key, value in instance.items()}
        elif isinstance(instance, tuple):
            vals = [cls._to_device(value, device=device) for value in instance]
            return type(instance)(*vals)
        else:
            try:
                return instance.to(device)
            except Exception as e:
                raise(e, f"{type(instance)} not recognized for cuda")

    def _train_step(self, model, f_loss, batch, optimizer, scheduler=None):
        output = f_loss(batch)
        if isinstance(output, dict):
            loss = output.pop("loss")
        else:
            loss = output
        if len(loss.size()) >= 1:
            loss = loss.mean()
        loss.backward()
        self.accumulated_steps += 1
        if self.accumulated_steps == self.accumulation_step:
            torch.nn.utils.clip_grad_norm_(model.parameters(), self.max_grad_norm)
            optimizer.step()
            optimizer.zero_grad()
            self.accumulated_steps = 0
            self.optimization_step += 1
            if scheduler:
                scheduler.step()
        if isinstance(output, dict):
            return loss, output
        else:
            return loss

    def run_one_epoch(self, model, loader, split, f_loss=None, f_metrics=None, optimizer=None, scheduler=None, collect_outputs=None, metric=None, max_steps:int=-1, loss_validation:Union[None, Callable]=lambda t:t>0, **kwargs):
        if f_loss is None:
            f_loss = model.forward
        if split == "train":
            model.train()
            if optimizer is None:
                raise ValueError("training requires valid optimizer")
            optimizer.zero_grad()
            if self.epoch == 0 and self.train_iterator is None:
                for _ in loader:
                    pass
        else:
            model.eval()
        epoch_loss = Record()
        epoch_metric = self.metric()
        record_metric = True
        self.accumulated_steps = 0
        if collect_outputs is not None:
            self.epoch_outputs = {key: [] for key in collect_outputs}
        tot = len(loader)
        iterator = None
        if split != "train" or self.train_iterator is None:
            info = ""
            if kwargs is not None:
                info += (" ".join([f"{k}: {v}" for k, v in kwargs.items()]) + '|')
            if split != "train":
                iterator = tqdm(loader, f"{info} Epoch {self.epoch:3d} / {self.train_epoch:3d}: {split[:5]:5s}|", total=tot, ncols=128)
            else:
                iterator = tqdm(loader, f"{info} Epoch {self.epoch+1:3d} / {self.train_epoch:3d}: {split[:5]:5s}|", total=tot, ncols=128)
            iterator = (enumerate(iterator), iterator)
            if split == "train":
                self.epoch += 1
                self.train_iterator = iterator
        else:
            iterator = self.train_iterator
        
        last_it = self.train_last_it if split == "train" else -1
        it = -1
        while max_steps < 0 or (it - last_it) < max_steps:
            try:
                it, batch = next(iterator[0])
            except StopIteration as e:
                if split == "train":
                    self.train_iterator = None
                break
            if not self.no_gpu and not self.distributed:
                batch = self._to_device(batch, torch.device(f"cuda:0"))
            if split == "train":
                output = self._train_step(model=model, f_loss=f_loss, batch=batch, optimizer=optimizer, scheduler=scheduler)
                if isinstance(output, tuple):
                    loss, output = output
                else:
                    loss = output
                    
            else:
                with torch.no_grad():
                    output = f_loss(batch)
                if isinstance(output, dict):
                    loss = output.pop("loss")
                    if len(loss.size()) > 0:
                        loss = loss.mean()
                    output = {k: v.cpu() for k, v in output.items()}
                else:
                    loss = output
            model_output = output
            for key in self.epoch_outputs:
                if key in output:
                    self.epoch_outputs[key].append(model_output[key])
            if loss_validation(loss.item()):
                epoch_loss += loss.item()
                if metric in model_output and record_metric:
                    metric_val = model_output[metric]
                    if isinstance(metric_val, torch.Tensor):
                        metric_val = metric_val.numpy()
                        if metric == "f1" and len(metric_val.shape) > 1:
                            metric_val = np.sum(metric_val, axis=0)
                        if metric == "accuracy" and len(metric_val.shape) > 0:
                            metric_val = np.sum(metric_val, axis=0)
                    epoch_metric += metric_val
                else:
                    # epoch_metric += f_metrics(model_output)
                    record_metric = False
            else:
                print(f"something goes wrong. {loss.item()}")
            if record_metric:
                postfix = {"loss": f"{epoch_loss}", "metric": f"{epoch_metric}"}
            else:
                postfix = {"loss": f"{epoch_loss}"}
            iterator[1].set_postfix(postfix)
            if max_steps > 0 and it - last_it == max_steps:
                break
        if split == "train":
            if self.train_iterator is None:
                self.train_last_it = -1
            else:
                self.train_last_it = it
        
        return epoch_loss, epoch_metric if record_metric else None

    def save(self,
        model:Union[torch.nn.Module, Dict],
        optimizer:Union[torch.optim.Optimizer, Dict, None]=None,
        scheduler:Union[torch.optim.lr_scheduler._LRScheduler, Dict, None]=None,
        postfix:str=""):

        save_dirs = self.log_dir
        if not os.path.exists(save_dirs):
            os.makedirs(save_dirs)
        def get_state_dict(x):
            if x is None:
                return None
            elif isinstance(x, dict):
                return x
            else:
                try:
                    return x.state_dict()
                except Exception as e:
                    raise ValueError(f"model, optimizer or scheduler to save must be either a dict or have callable state_dict method")
        if postfix is not "":
            save_model = os.path.join(save_dirs, f"{self.save_model}.{postfix}")
        else:
            save_model = os.path.join(save_dirs, self.save_model)
        torch.save({
            "state_dict": get_state_dict(model),
            "optimizer_state_dict": get_state_dict(optimizer),
            "scheduler_state_dict": get_state_dict(scheduler),
            "iter": self.epoch + 1
            },
            save_model
        )

    def load(self, model:torch.nn.Module, optimizer:Union[torch.optim.Optimizer, None]=None, scheduler:Union[torch.optim.lr_scheduler._LRScheduler,None]=None, path:Union[str, None]=None, load_iter:bool=True, strict:bool=True) -> None:
        if path is None:
            path = self.load_model
        if not os.path.exists(path):
            raise FileNotFoundError(f"the path {path} to saved model is not correct")

        state_dict = torch.load(path, map_location=torch.device('cuda:0') if torch.cuda.is_available() and (not self.no_gpu) else torch.device('cpu'))
        model.load_state_dict(state_dict=state_dict["state_dict"], strict=strict)
        if load_iter:
            self.epoch = state_dict["iter"] - 1
        if optimizer:
            optimizer.load_state_dict(state_dict=state_dict["optimizer_state_dict"])
        if scheduler:
            scheduler.load_state_dict(state_dict=state_dict["scheduler_state_dict"])
        return None

class GWorker(Worker):

    def __init__(self, opts):
        super().__init__(opts)
        self.ref_grads = None
    
    def _apply(self, model, func:str, *args, **kwargs):
        if hasattr(model, func):
            return getattr(model, func)(*args, **kwargs)
        else:
            return getattr(self, func)(model, *args, **kwargs)

    def _train_step(self, model, f_loss, batch, optimizer, scheduler=None):
        output = f_loss(batch)
        if isinstance(output, dict):
            loss = output.pop("loss")
        else:
            loss = output
        if self.accumulation_step > 1:
            loss = loss / self.accumulation_step
        if len(loss.size()) >= 1:
            loss = loss.mean()
        loss.backward()
        ref_output = self._apply(model, 'compute_ref_loss', batch)
        if isinstance(ref_output, dict):
            ref_loss = ref_output.pop("loss")
        else:
            ref_loss = ref_output
        if len(ref_loss.size()) >= 1:
            ref_loss = ref_loss.mean()
        self._apply(model, 'update_ref_gradient', ref_loss / self.accumulation_step)
        self.accumulated_steps += 1
        if self.accumulated_steps == self.accumulation_step:
            self._apply(model, 'update_gradient')
            torch.nn.utils.clip_grad_norm_(model.parameters(), self.max_grad_norm)
            optimizer.step()
            optimizer.zero_grad()
            self.accumulated_steps = 0
            self.optimization_step += 1
            if scheduler:
                scheduler.step()
        if isinstance(output, dict):
            return loss, output
        else:
            return loss
    
    def compute_ref_loss(self, model, batch, *args, **kwargs):
        ref_batch = {k[4:]: v for k,v in batch.items() if k.startswith("ref_")}
        output = model(ref_batch, *args, **kwargs)
        return output

    def update_ref_gradient(self, model, ref_loss:torch.FloatTensor):
        named_params = [(name, param) for name, param in model.named_parameters() if param.requires_grad]
        params = [param for name, param in named_params]
        names = [name for name, param in named_params]
        grads = torch.autograd.grad(ref_loss, params, allow_unused=True)
        with torch.no_grad():
            if self.ref_grads is None:
                self.ref_grads = {name: ref_grad.data for name, ref_grad in zip(names, grads) if ref_grad is not None}
            else:
                for name, ref_grad in zip(names, grads):
                    if ref_grad is not None:
                        self.ref_grads[name] += ref_grad.data

    def update_gradient(self, model, epsilon:float=0.):
        if self.ref_grads is None:
            warnings.warn("no grad, maybe error in running.")
            return False
        if epsilon >= 1:
            w = 0.5
        if epsilon <= -1:
            w = 1
        named_params = [(name, param) for name, param in model.named_parameters() if param.requires_grad]
        numer = 0
        denom = 0
        gnorm = 0
        with torch.no_grad():
            for name, param in named_params:
                if name in self.ref_grads:
                    ref_grad = self.ref_grads[name]
                    numer += torch.sum(param.grad * ref_grad)
                    denom += torch.sum(ref_grad * ref_grad)
                    gnorm += torch.sum(param.grad * param.grad)
            if denom < 1e-10:
                return
            w = numer / denom
            if epsilon > 0:
                w += epsilon * torch.sqrt(gnorm / denom)
            w = w.item()
            if w > 0.:
                w = 0.3
            else:
                w = 1.
            for name, param in named_params:
                if param.grad is not None:
                    param.grad.data = (1-w) * param.grad.data + w * self.ref_grads[name]
        self.ref_grads = None
        return w > 0