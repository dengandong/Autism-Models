#for DATA in ESDB SSDB
#do
#	bash tools/dist_train.sh  configs/recognition/swin/swin_base_patch244_window877_$DATA.py 4 \
#	--cfg-options total_epochs=50 \
#	work_dir=new_work_dirs/${DATA}_pretrained/ \
#	load_from=swin_base_patch244_window877_kinetics600_22k.pth \
#	data.train.ann_file=data/$DATA/new_annotations/${DATA}_train.txt \
#	data.val.ann_file=data/$DATA/new_annotations/${DATA}_test.txt \
#  data.test.ann_file=data/$DATA/new_annotations/${DATA}_test.txt
#done
#
#for DATA in ESDB SSDB
#do
#	bash tools/dist_train.sh  configs/recognition/swin/swin_base_patch244_window877_$DATA.py 4 \
#	--cfg-options total_epochs=100 \
#	work_dir=new_work_dirs/${DATA}_no_pretrained/ \
#	data.train.ann_file=data/$DATA/new_annotations/${DATA}_train.txt \
#	data.val.ann_file=data/$DATA/new_annotations/${DATA}_test.txt \
#  data.test.ann_file=data/$DATA/new_annotations/${DATA}_test.txt
#done

for DATA in ESDB SSDB
do
	bash tools/dist_train.sh  configs/recognition/swin/swin_base_patch244_window877_${DATA}_contrastive.py 4 \
	--cfg-options total_epochs=50 \
	work_dir=new_work_dirs/${DATA}_pretrained_contrastive/ \
	load_from=swin_base_patch244_window877_kinetics600_22k.pth \
	data.train.ann_file=data/$DATA/new_annotations/${DATA}_train.txt \
	data.val.ann_file=data/$DATA/new_annotations/${DATA}_test.txt \
  data.test.ann_file=data/$DATA/new_annotations/${DATA}_test.txt
done

for DATA in ESDB SSDB
do
	bash tools/dist_train.sh  configs/recognition/swin/swin_base_patch244_window877_${DATA}_contrastive.py 4 \
	--cfg-options total_epochs=100 \
	work_dir=new_work_dirs/${DATA}_no_pretrained_contrastive/ \
	data.train.ann_file=data/$DATA/new_annotations/${DATA}_train.txt \
	data.val.ann_file=data/$DATA/new_annotations/${DATA}_test.txt \
  data.test.ann_file=data/$DATA/new_annotations/${DATA}_test.txt
done

bash tools/dist_train.sh  configs/recognition/swin/swin_base_patch244_window877_joint.py 4 \
--cfg-options total_epochs=50 \
work_dir=new_work_dirs/joint_pretrained/ \
load_from=swin_base_patch244_window877_kinetics600_22k.pth \
data.train.ann_file=data/Joint/Joint_train.txt \
data.val.ann_file=data/Joint/Joint_test.txt \
data.test.ann_file=data/Joint/Joint_test.txt

bash tools/dist_train.sh  configs/recognition/swin/swin_base_patch244_window877_joint_contrastive.py 4 \
--cfg-options total_epochs=50 \
work_dir=new_work_dirs/joint_pretrained_contrastive/ \
load_from=swin_base_patch244_window877_kinetics600_22k.pth \
data.train.ann_file=data/Joint/Joint_train.txt \
data.val.ann_file=data/Joint/Joint_test.txt \
data.test.ann_file=data/Joint/Joint_test.txt
