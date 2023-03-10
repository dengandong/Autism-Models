bash tools/dist_train.sh  configs/recognition/swin/swin_base_patch244_window877_joint.py 4 --cfg-options total_epochs=50 work_dir='new_work_dirs/Joint_pretrain' load_from=swin_base_patch244_window877_kinetics600_22k.pth
bash tools/dist_train.sh  configs/recognition/swin/swin_base_patch244_window877_joint_contrastive.py 4 --cfg-options total_epochs=100 work_dir='.work_dirs/Joint_contrastive' 
bash tools/dist_train.sh  configs/recognition/swin/swin_base_patch244_window877_joint.py 4 --cfg-options total_epochs=100 work_dir='.work_dirs/Joint' 
