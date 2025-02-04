import os
import shutil
from tqdm.auto import tqdm

base_path = "./audioPianoTriadDataset/audioPianoTriadDataset/audio_augmented_x10"
dst_path = "./splitted_each"
dataset = os.listdir(base_path)

classes = set()

for data in tqdm(dataset):
    name_file = data.split("_")
    name_file.pop()
    # name_file.pop()
    classes.add("_".join(name_file))

classes = list(classes)
for cls in classes:
    cls_path = os.path.join(dst_path, cls)
    # print(cls_path)
    os.mkdir(cls_path)
    
for data in tqdm(dataset):
    name_file = data.split("_")
    name_file.pop()
    # name_file.pop() 
    dst = classes[classes.index("_".join(name_file))]
    dst = os.path.join(dst_path, dst)
    file_path = os.path.join(base_path, data)
    shutil.copy(file_path, dst)
    
