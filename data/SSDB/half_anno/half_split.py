import os
import random

train_file = open('SSDB_old_train.txt', 'r')
test_file = open('SSDB_old_test.txt', 'r')

content = train_file.readlines() + test_file.readlines()
print(len(content))

data_dict = dict()

for line in content:
    video_name = line.split(' ')[0]
    class_name = video_name.split('/')[5].split('_0')[0]
    assert class_name in ['Arm_Flapping', 'Head_Banging', 'Hand_Action', 'Spinning'], '{}'.format(class_name)
    if class_name in data_dict.keys():
        data_dict[class_name].append(line)
    else:
        data_dict[class_name] = [line]

print(data_dict.keys())
train_content = []
test_content = []
for key in data_dict.keys():
    selected = random.sample(data_dict[key], len(data_dict[key])//2)
    train_content.extend(selected)
    test_content.extend(list(set(data_dict[key]) - set(selected)))

print(len(train_content))
print(len(test_content))

new_train = open('SSDB_train.txt', 'w')
new_test = open('SSDB_test.txt', 'w')

for line in train_content:
    new_train.write(line)

for line in test_content:
    new_test.write(line)

