# Autism-Models

## Install
PyTorch: 1.7, Torchvision: 0.8
create your env, the version of your cudatoolkit depends on your GPUs, 
refer to [this](https://pytorch.org/get-started/previous-versions/) for more options:

`conda create -n autism python=3.8 pytorch=1.7 cudatoolkit=${YOUR_CUDATOOLKIT} torchvision -c pytorch -y`

Install mmcv-full following this:

`pip3 install openmim`

`mim install mmcv-full`

You can use the follow command to install video-swin version of MMAction:

`pip install -v -e . --user`


## Datasets
You can refer to [this](https://github.com/open-mmlab/mmaction2/blob/master/docs/en/tutorials/3_new_dataset.md) to prepare new datasets for model training.

## Model training
Modify your own config files [here](https://github.com/dengandong/Autism-Models/tree/main/configs/recognition/swin) 
THe pretrained model swin_base_patch244_window877_kinetics600_22k.pth can be downloaded [here](https://github.com/SwinTransformer/storage/releases/download/v1.0.4/swin_base_patch244_window877_kinetics600_22k.pth).

Multiple GPUs:
`bash tools/dist_train.sh  
configs/recognition/swin/swin_base_patch244_window877_joint.py 4 
--cfg-options total_epochs=50 work_dir='new_work_dirs/Joint_pretrain' load_from=swin_base_patch244_window877_kinetics600_22k.pth`

Single GPU:
`python tools/train.py 
configs/recognition/swin/swin_base_patch244_window877_joint.py 
--cfg-options total_epochs=50 work_dir='new_work_dirs/Joint_pretrain' load_from=swin_base_patch244_window877_kinetics600_22k.pth`

## Model Test
Once you finish training your model, you can test your model with:
`bash tools/dist_test.sh 
configs/recognition/swin/swin_base_patch244_window877_${DATA}.py 
new_work_dirs/${DATA}_pretrained/best_mean_class_accuracy_epoch* 4 
--cfg-options data.test.ann_file=data/${DATA}/new_annotations/${DATA}_test.txt --eval top_k_accuracy`