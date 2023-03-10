for DATA in ESDB SSDB
do
  echo "dataset: ${DATA}, no pretrained/ no contrastive"
	bash tools/dist_test.sh configs/recognition/swin/swin_base_patch244_window877_${DATA}.py new_work_dirs/${DATA}_no_pretrained/best_mean_class_accuracy_epoch* 4 --cfg-options data.test.ann_file=data/${DATA}/new_annotations/${DATA}_test.txt --eval top_k_accuracy
done

for DATA in ESDB SSDB
do
  echo "dataset: ${DATA}, pretrained/ no contrastive"
	bash tools/dist_test.sh configs/recognition/swin/swin_base_patch244_window877_${DATA}.py new_work_dirs/${DATA}_pretrained/best_mean_class_accuracy_epoch* 4 --cfg-options data.test.ann_file=data/${DATA}/new_annotations/${DATA}_test.txt --eval top_k_accuracy
done

for DATA in ESDB SSDB
do
  echo "dataset: ${DATA}, no pretrained/ contrastive"
	bash tools/dist_test.sh configs/recognition/swin/swin_base_patch244_window877_${DATA}_contrastive.py new_work_dirs/${DATA}_no_pretrained/best_mean_class_accuracy_epoch* 4 --cfg-options data.test.ann_file=data/${DATA}/new_annotations/${DATA}_test.txt --eval top_k_accuracy
done

for DATA in ESDB SSDB
do
	echo "dataset: ${DATA}, pretrained/ contrastive"
  bash tools/dist_test.sh configs/recognition/swin/swin_base_patch244_window877_${DATA}_contrastive.py new_work_dirs/${DATA}_pretrained/best_mean_class_accuracy_epoch* 4 --cfg-options data.test.ann_file=data/${DATA}/new_annotations/${DATA}_test.txt --eval top_k_accuracy
done

#echo "dataset: joint, no pretrained/ contrastive"
#bash tools/dist_test.sh configs/recognition/swin/swin_base_patch244_window877_joint.py new_work_dirs/joint_no_pretrained/best_mean_class_accuracy_epoch_* 4 --cfg-options data.test.ann_file=data/Joint/Joint_test.txt --eval top_k_accuracy
