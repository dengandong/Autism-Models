import torch
import torch.nn.functional as F


class GradCAM:
    """GradCAM class helps create visualization results.

    Visualization results are blended by heatmaps and input images.
    This class is modified from
    https://github.com/facebookresearch/SlowFast/blob/master/slowfast/visualization/gradcam_utils.py # noqa
    For more information about GradCAM, please visit:
    https://arxiv.org/pdf/1610.02391.pdf
    """

    def __init__(self, model, target_layer_name, colormap='bwr'):
        """Create GradCAM class with recognizer, target layername & colormap.

        Args:
            model (nn.Module): the recognizer model to be used.
            target_layer_name (str): name of convolutional layer to
                be used to get gradients and feature maps from for creating
                localization maps.
            colormap (Optional[str]): matplotlib colormap used to create
                heatmap. Default: 'viridis'. For more information, please visit
                https://matplotlib.org/3.3.0/tutorials/colors/colormaps.html
        """
        from ..models.recognizers import Recognizer2D, Recognizer3D
        if isinstance(model, Recognizer2D):
            self.is_recognizer2d = True
        elif isinstance(model, Recognizer3D):
            self.is_recognizer2d = False
        else:
            raise ValueError(
                'GradCAM utils only support Recognizer2D & Recognizer3D.')

        self.model = model
        self.model.eval()
        self.target_gradients = None
        self.target_activations = None

        import matplotlib.pyplot as plt
        self.colormap = plt.get_cmap(colormap)
        self.data_mean = torch.tensor(model.cfg.img_norm_cfg['mean'])
        self.data_std = torch.tensor(model.cfg.img_norm_cfg['std'])
        self._register_hooks(target_layer_name)

    def _register_hooks(self, layer_name):
        """Register forward and backward hook to a layer, given layer_name, to
        obtain gradients and activations.

        Args:
            layer_name (str): name of the layer.
        """

        def get_gradients(module, grad_input, grad_output):
            self.target_gradients = grad_output[0].detach()

        def get_activations(module, input, output):
            self.target_activations = output.clone().detach()

        layer_ls = layer_name.split('/')
        prev_module = self.model
        for layer in layer_ls:
            prev_module = prev_module._modules[layer]

        target_layer = prev_module
        target_layer.register_forward_hook(get_activations)
        # target_layer.register_backward_hook(get_gradients)

    def _calculate_localization_map(self, inputs, use_labels, delta=1e-20):
        """Calculate localization map for all inputs with Grad-CAM.

        Args:
            inputs (dict): model inputs, generated by test pipeline,
                at least including two keys, ``imgs`` and ``label``.
            use_labels (bool): Whether to use given labels to generate
                localization map. Labels are in ``inputs['label']``.
            delta (float): used in localization map normalization,
                must be small enough. Please make sure
                `localization_map_max - localization_map_min >> delta`
        Returns:
            tuple[torch.Tensor, torch.Tensor]: (localization_map, preds)
                localization_map (torch.Tensor): the localization map for
                    input imgs.
                preds (torch.Tensor): Model predictions for `inputs` with
                    shape (batch_size, num_classes).
        """
        inputs['imgs'] = inputs['imgs'].clone()

        # model forward & backward
        with torch.no_grad():
            preds = self.model(gradcam=True, **inputs)
        if use_labels:
            labels = inputs['label']
            if labels.ndim == 1:
                labels = labels.unsqueeze(-1)
            score = torch.gather(preds, dim=1, index=labels)
        else:
            score = torch.max(preds, dim=-1)[0]
        # self.model.zero_grad()
        # score = torch.sum(score)
        # score.backward()

        if self.is_recognizer2d:
            # [batch_size, num_segments, 3, H, W]
            b, t, _, h, w = inputs['imgs'].size()
        else:
            # [batch_size, num_crops*num_clips, 3, clip_len, H, W]
            b1, b2, ch, t, h, w = inputs['imgs'].size()
            print(b1, b2, ch, t, h, w)
            b = b1 * b2

        # gradients = self.target_gradients
        activations = self.target_activations
        attn_map = self.model.backbone.attn_map
        print('attn_map size: ', attn_map.size())

        # 1. average for all heads
        attn_map = torch.mean(attn_map, dim=1)
        # 2. inverse transform from window to ex-window
        # in this layer, the feature transform like: (1, 16, 14, 14, 512) --> (1, 2, 8, 2, 7, 2, 7, 512) --> (2^3, 8*7*7, 512) -->
        # --> q: (8, 16, 392, 512 // 16)  --> attn_map: (8, 16, 392, 392)
        # thus: averaged attn_map (8, 392, 392) needs transforming to ?
        attn = torch.max(attn_map, dim=-2)[0] # 8, 392 or max
        attn = attn.view(-1, 8, 7, 7)  # 8, 8, 7, 7
        attn = attn.view(-1, 2, 2, 2, 8, 7, 7).permute(0, 1, 4, 2, 5, 3, 6)
        print(attn.size())
        attn = attn.contiguous().view(-1, 16, 14, 14).unsqueeze(1)
        # print('reshape attn size: ', attn.size())

        attn = F.interpolate(
            attn,
            size=(t, h, w),
            mode='trilinear',
            align_corners=False)

        # Normalize the localization map.
        localization_map_min, localization_map_max = (
            torch.min(attn.view(b, -1), dim=-1, keepdim=True)[0],
            torch.max(attn.view(b, -1), dim=-1, keepdim=True)[0])
        localization_map_min = torch.reshape(
            localization_map_min, shape=(b, 1, 1, 1, 1))
        localization_map_max = torch.reshape(
            localization_map_max, shape=(b, 1, 1, 1, 1))
        localization_map = (attn - localization_map_min) / (
            localization_map_max - localization_map_min + delta)
        attn_output = localization_map.data

        # if self.is_recognizer2d:
        #     # [B*Tg, C', H', W']
        #     # b_tg, c, _, _ = gradients.size()
        #     # tg = b_tg // b
        #     pass
        # else:
        #     # source shape: [B, C', Tg, H', W']
        #     # _, c, tg, _, _ = gradients.size()
        #     # target shape: [B, Tg, C', H', W']
        #     # gradients = gradients.permute(0, 2, 1, 3, 4)
        #     print(activations.size())
        #     activations = activations.permute(0, 1, 4, 2, 3)
        #
        # # calculate & resize to [B, 1, T, H, W]
        # # weights = torch.mean(gradients.view(b, tg, c, -1), dim=3)
        # # weights = weights.view(b, tg, c, 1, 1)
        # # activations = activations.view([b, tg, c] +
        # #                                list(activations.size()[-2:]))
        # # localization_map = torch.sum(
        # #     weights * activations, dim=2, keepdim=True)
        # localization_map = torch.sum(activations, dim=2, keepdim=True)
        # localization_map = F.relu(localization_map)
        # localization_map = localization_map.permute(0, 2, 1, 3, 4)
        # localization_map = F.interpolate(
        #     localization_map,
        #     size=(t, h, w),
        #     mode='trilinear',
        #     align_corners=False)
        #
        # # Normalize the localization map.
        # localization_map_min, localization_map_max = (
        #     torch.min(localization_map.view(b, -1), dim=-1, keepdim=True)[0],
        #     torch.max(localization_map.view(b, -1), dim=-1, keepdim=True)[0])
        # localization_map_min = torch.reshape(
        #     localization_map_min, shape=(b, 1, 1, 1, 1))
        # localization_map_max = torch.reshape(
        #     localization_map_max, shape=(b, 1, 1, 1, 1))
        # localization_map = (localization_map - localization_map_min) / (
        #     localization_map_max - localization_map_min + delta)
        # localization_map = localization_map.data

        print('interp:', attn_output.shape)
        return attn_output.squeeze(dim=1), preds

    def _alpha_blending(self, localization_map, input_imgs, alpha):
        """Blend heatmaps and model input images and get visulization results.

        Args:
            localization_map (torch.Tensor): localization map for all inputs,
                generated with Grad-CAM
            input_imgs (torch.Tensor): model inputs, normed images.
            alpha (float): transparency level of the heatmap,
                in the range [0, 1].
        Returns:
            torch.Tensor: blending results for localization map and input
                images, with shape [B, T, H, W, 3] and pixel values in
                RGB order within range [0, 1].
        """
        # localization_map shape [B, T, H, W]
        localization_map = localization_map.cpu()

        # heatmap shape [B, T, H, W, 3] in RGB order
        heatmap = self.colormap(localization_map.detach().numpy())
        heatmap = heatmap[:, :, :, :, :3]
        heatmap = torch.from_numpy(heatmap)

        # Permute input imgs to [B, T, H, W, 3], like heatmap
        if self.is_recognizer2d:
            # Recognizer2D input (B, T, C, H, W)
            curr_inp = input_imgs.permute(0, 1, 3, 4, 2)
        else:
            # Recognizer3D input (B', num_clips*num_crops, C, T, H, W)
            # B = B' * num_clips * num_crops
            curr_inp = input_imgs.view([-1] + list(input_imgs.size()[2:]))
            curr_inp = curr_inp.permute(0, 2, 3, 4, 1)

        # renormalize input imgs to [0, 1]
        curr_inp = curr_inp.cpu()
        curr_inp *= self.data_std
        curr_inp += self.data_mean
        curr_inp /= 255.

        # alpha blending
        blended_imgs = alpha * heatmap + (1 - alpha) * curr_inp

        return blended_imgs

    def __call__(self, inputs, use_labels=False, alpha=0.5):
        """Visualize the localization maps on their corresponding inputs as
        heatmap, using Grad-CAM.

        Generate visualization results for **ALL CROPS**.
        For example, for I3D model, if `clip_len=32, num_clips=10` and
        use `ThreeCrop` in test pipeline, then for every model inputs,
        there are 960(32*10*3) images generated.

        Args:
            inputs (dict): model inputs, generated by test pipeline,
                at least including two keys, ``imgs`` and ``label``.
            use_labels (bool): Whether to use given labels to generate
                localization map. Labels are in ``inputs['label']``.
            alpha (float): transparency level of the heatmap,
                in the range [0, 1].
        Returns:
            blended_imgs (torch.Tensor): Visualization results, blended by
                localization maps and model inputs.
            preds (torch.Tensor): Model predictions for inputs.
        """

        # localization_map shape [B, T, H, W]
        # preds shape [batch_size, num_classes]
        localization_map, preds = self._calculate_localization_map(
            inputs, use_labels=use_labels)

        # blended_imgs shape [B, T, H, W, 3]
        blended_imgs = self._alpha_blending(localization_map, inputs['imgs'],
                                            alpha)

        # blended_imgs shape [B, T, H, W, 3]
        # preds shape [batch_size, num_classes]
        # Recognizer2D: B = batch_size, T = num_segments
        # Recognizer3D: B = batch_size * num_crops * num_clips, T = clip_len
        return blended_imgs, preds
