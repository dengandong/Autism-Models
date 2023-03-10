import torch
import torch.nn as nn
from mmcv.cnn import normal_init
from ...core import top_k_accuracy

from ..builder import HEADS
from ..builder import build_loss

# import clip

# clip_model, _ = clip.load("ViT-B/32", device='cuda')
# text = ['Arm Flapping', 'Head Banging', 'Spinning', 'Hand Action']
# tt_list = list()
# for tt in text:
#     tt = clip.tokenize(tt).to('cuda')
#     tt = clip_model.encode_text(tt)
#     tt_list.append(tt)



@HEADS.register_module()
class ContranstiveHead(nn.Module):
    """Classification head for I3D.

    Args:
        num_classes (int): Number of classes to be classified.
        in_channels (int): Number of channels in input feature.
        loss_cls (dict): Config for building loss.
            Default: dict(type='CrossEntropyLoss')
        spatial_type (str): Pooling type in spatial dimension. Default: 'avg'.
        dropout_ratio (float): Probability of dropout layer. Default: 0.5.
        init_std (float): Std value for Initiation. Default: 0.01.
        kwargs (dict, optional): Any keyword argument to be used to initialize
            the head.
    """

    def __init__(self,
                 num_classes,
                 in_channels,
                 loss_cls=dict(type='CrossEntropyLoss'),
                 spatial_type='avg',
                 dropout_ratio=0.5,
                 init_std=0.01,
                 ):
        super().__init__()

        self.num_classes = num_classes
        self.spatial_type = spatial_type
        self.dropout_ratio = dropout_ratio
        self.in_channels = in_channels
        self.loss_cls = build_loss(loss_cls)
        self.multi_class = False

        self.init_std = init_std
        if self.dropout_ratio != 0:
            self.dropout = nn.Dropout(p=self.dropout_ratio)
        else:
            self.dropout = None
        self.fc_cls = nn.Linear(self.in_channels, self.num_classes)

        if self.spatial_type == 'avg':
            # use `nn.AdaptiveAvgPool3d` to adaptively match the in_channels.
            self.avg_pool = nn.AdaptiveAvgPool3d((1, 1, 1))
        else:
            self.avg_pool = None

        self.projector = nn.Linear(512, self.in_channels)
        self.cosine_similarity = nn.CosineSimilarity(dim=1).cuda()

    def init_weights(self):
        """Initiate the parameters from scratch."""
        normal_init(self.fc_cls, std=self.init_std)

    def forward(self, x):
        """Defines the computation performed at every call.

        Args:
            x (torch.Tensor): The input visual feature.

        Returns:
            torch.Tensor: The classification scores for input samples.
        """
        # [N, in_channels, 4, 7, 7]
        if self.avg_pool is not None:
            x = self.avg_pool(x)
        # [N, in_channels, 1, 1, 1]
        if self.dropout is not None:
            x = self.dropout(x)
        # [N, in_channels, 1, 1, 1]
        x = x.view(x.shape[0], -1)

        # [N, in_channels]
        cls_score = self.fc_cls(x)
        # [N, num_classes]
        return cls_score, x

    def loss(self, cls_score, x, labels, **kwargs):
        """Calculate the loss given output ``cls_score``, target ``labels``.

        Args:
            x: visual feature
            cls_score (torch.Tensor): The output of the model.
            labels (torch.Tensor): The target output of the model.

        Returns:
            dict: A dict containing field 'loss_cls'(mandatory)
            and 'top1_acc', 'top5_acc'(optional).
        """
        losses = dict()
        if labels.shape == torch.Size([]):
            labels = labels.unsqueeze(0)
        elif labels.dim() == 1 and labels.size()[0] == self.num_classes \
                and cls_score.size()[0] == 1:
            # Fix a bug when training with soft labels and batch size is 1.
            # When using soft labels, `labels` and `cls_socre` share the same
            # shape.
            labels = labels.unsqueeze(0)

        if not self.multi_class and cls_score.size() != labels.size():
            top_k_acc = top_k_accuracy(cls_score.detach().cpu().numpy(),
                                       labels.detach().cpu().numpy(), (1, 5))
            losses['top1_acc'] = torch.tensor(
                top_k_acc[0], device=cls_score.device)
            losses['top5_acc'] = torch.tensor(
                top_k_acc[1], device=cls_score.device)

        elif self.multi_class and self.label_smooth_eps != 0:
            labels = ((1 - self.label_smooth_eps) * labels +
                      self.label_smooth_eps / self.num_classes)

        loss_cls = self.loss_cls(cls_score, labels, **kwargs)

        # if labels == 0:
        #     y = 'Arm Flapping'
        # elif labels == 1:
        #     y = 'Head Banging'
        # elif labels == 2:
        #     y = 'Spinning'
        # elif labels == 3:
        #     y = 'Hand Action'
        # else:
        #     raise NotImplementedError

        # print(labels)
        features = torch.load('/home/dengandong/Research/Autism/description_features.pth').to('cuda')
        y = features[labels]
        # print(y)

        # [N, in_channels]
        y = self.projector(y)
        loss_contrastive = - self.cosine_similarity(x, y).mean()
        # loss_cls may be dictionary or single tensor
        if isinstance(loss_cls, dict):
            losses.update(loss_cls)
        else:
            losses['loss_cls'] = loss_cls
            losses['loss_contrastive'] = loss_contrastive

        return losses
