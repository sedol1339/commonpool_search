from pathlib import Path
import tarfile
from tqdm import tqdm

imagenet_classes = dict(zip(
    open('imagenet21k_wordnet_ids.txt').read().split('\n'),
    open('imagenet21k_wordnet_lemmas.txt').read().split('\n')
))

counts = {}

for cls_code, cls_name in tqdm(imagenet_classes.items()):
    file = Path(f'winter21_whole/{cls_code}.tar')
    if file.is_file():
        with tarfile.open(file, 'r:*') as f:
            image_filenames = f.getnames()
            counts[cls_name] = len(image_filenames)
        with open(f'winter21_whole/{cls_code}_count.txt', 'w') as f:
            f.write(str(counts[cls_name]))
        file.rename(file.with_suffix('.done.tar'))