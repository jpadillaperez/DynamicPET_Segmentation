# Inspired by: https://github.com/pytorch/pytorch/issues/50334

import torch
import torch.nn as nn
from torch import Tensor
from torch.optim.lr_scheduler import _LRScheduler

def torch_interp_1d(x: Tensor, xp: Tensor, fp: Tensor) -> Tensor:
    """
    One-dimensional linear interpolation for monotonically increasing sample
    points.

    Returns the one-dimensional piecewise linear interpolant to a function with
    given discrete data points :math:`(xp, fp)`, evaluated at :math:`x`.

    Args:
        x: the :math:`x`-coordinates at which to evaluate the interpolated
            values.
        xp: the :math:`x`-coordinates of the data points, must be increasing.
        fp: the :math:`y`-coordinates of the data points, same length as `xp`.

    Returns:
        the interpolated values, same size as `x`.
    """
    m = (fp[1:] - fp[:-1]) / (xp[1:] - xp[:-1])
    b = fp[:-1] - (m * xp[:-1])

    indexes = torch.sum(torch.ge(x[:, None], xp[None, :]), 1) - 1
    indexes = torch.clamp(indexes, 0, len(m) - 1)

    return m[indexes] * x + b[indexes]

def torch_interp_Nd(x: torch.Tensor, xp: torch.Tensor, fp: torch.Tensor) -> torch.Tensor:
    """
    One-dimensional linear interpolation for monotonically increasing sample
    points.

    Returns the one-dimensional piecewise linear interpolant to a function with
    given discrete data points :math:`(xp, fp)`, evaluated at :math:`x`.

    Args:
        x: the :math:`x`-coordinates at which to evaluate the interpolated
            values.
        xp: the :math:`x`-coordinates of the data points, must be increasing.
        fp: the :math:`y`-coordinates of the data points, same length as `xp`.

    Returns:
        the interpolated values, same size as `x`.
    """
    m = (fp[:,1:] - fp[:,:-1]) / (xp[:,1:] - xp[:,:-1])  #slope
    b = fp[:, :-1] - (m.mul(xp[:, :-1]) )

    indexes = torch.sum(torch.ge(x[:, :, None], xp[:, None, :]), -1) - 1  #torch.ge:  x[i] >= xp[i] ? true: false
    indexes = torch.clamp(indexes, 0, m.shape[-1] - 1)

    line_idx = torch.arange(len(indexes), device=indexes.device).view(-1, 1)
    line_idx = line_idx.expand(indexes.shape)
    return m[line_idx, indexes].mul(x) + b[line_idx, indexes]

def torch_conv(in1, in2):
  in1 = in1.unsqueeze(0).unsqueeze(0)
  in2 = in2.unsqueeze(0).unsqueeze(0)
  in1_flip = torch.flip(in1, (0, 2)) 
  out = torch.conv1d(in1_flip, in2, padding=in1.shape[2]) 
  out = out[0, 0, in1.shape[2]+1:]
  out = torch.flipud(out)
  return out
  
def torch_conv_batch(in1, in2):
  b, s, t = in1.shape
  o = torch.conv1d(torch.flip(in1, (0, 2)), in2, padding=in1.shape[2], groups=s)
  o = o[:, :, in1.shape[2]+1:]
  o = torch.flip(o, (0, 2))
  return o


class WarmupScheduler(_LRScheduler):
    def __init__(self, optimizer, total_epochs, warmup_epochs, last_epoch=-1):
        self.warmup_epochs = warmup_epochs
        self.total_epochs = total_epochs
        super(WarmupScheduler, self).__init__(optimizer, last_epoch)

    def get_lr(self):
        if self.last_epoch < self.warmup_epochs:
            return [base_lr * float(self.last_epoch) / self.warmup_epochs for base_lr in self.base_lrs]
        return [base_lr for base_lr in self.base_lrs]



def weights_init_kaiming(m):
    '''
    Initialize weights of the model using Kaiming initialization (He et al., 2015).
    '''
    # Initialize Conv3d and ConvTranspose3d layers
    if isinstance(m, nn.Conv3d) or isinstance(m, nn.ConvTranspose3d):
        nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu') # ReLU is fine also for ELU
        if m.bias is not None:
            nn.init.constant_(m.bias, 0)
    # Initialize BatchNorm3d layers
    elif isinstance(m, nn.BatchNorm3d):
        nn.init.constant_(m.weight, 1)
        nn.init.constant_(m.bias, 0)


def weights_init_xavier(m):
    '''
    Initialize weights of the model using Xavier initialization (Glorot et al., 2010).
    '''
    # Initialize Conv3d and ConvTranspose3d layers
    if isinstance(m, nn.Conv3d) or isinstance(m, nn.ConvTranspose3d):
        nn.init.xavier_normal_(m.weight)
        if m.bias is not None:
            nn.init.constant_(m.bias, 0)
    # Initialize BatchNorm3d layers
    elif isinstance(m, nn.BatchNorm3d):
        nn.init.constant_(m.weight, 1)
        nn.init.constant_(m.bias, 0)