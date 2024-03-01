import os
import argparse
from pathlib import Path
from tqdm import tqdm
import itertools

# os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
import huggingface_hub
from huggingface_hub import snapshot_download
# from huggingface_hub.utils.logging import set_verbosity
# set_verbosity(huggingface_hub.logging.CRITICAL)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--folder',
        help="Folder to download",
        default='obelics'
    )
    args = parser.parse_args()
    
    folder = args.folder
    
    resumes = 0
    while True:
        if resumes > 0:
            print(f'Resuming after connection error ({resumes})') #TODO fix, may be out-of-disk error
        try:
            snapshot_download(
                repo_id=f'HuggingFaceM4/OBELICS',
                repo_type='dataset',
                allow_patterns='*.parquet',
                local_dir=folder,
                cache_dir=folder + '/hf_cache',
                local_dir_use_symlinks=True,
                resume_download=True,
            )
            break
        except KeyboardInterrupt:
            raise
        except:
           resumes += 1
