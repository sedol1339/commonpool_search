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
        '--subset',
        help="CommonPool subset to download",
        choices=['small', 'medium', 'large', 'xlarge'],
        default='xlarge'
    )
    parser.add_argument(
        '--folder',
        help="Folder to download",
        default='{subset}'
    )
    parser.add_argument(
        '--part',
        help="Part of xlarge subset (0 to 7)",
        type=int,
        default=-1,
    )
    args = parser.parse_args()
    
    subset = args.subset
    folder = args.folder if args.folder != '{subset}' else subset
    
    resumes = 0
    while True:
        if resumes > 0:
            print(f'Resuming after connection error ({resumes})') #TODO fix, may be out-of-disk error
        try:
            if subset == 'xlarge':
                if args.part == -1:
                    allow_patterns='part_0/*.parquet'
                else:
                    allow_patterns=f'part_{args.part}/*.parquet'
            else:
                allow_patterns='*.parquet'
            snapshot_download(
                repo_id=f'mlfoundations/datacomp_{subset}',
                repo_type='dataset',
                allow_patterns=allow_patterns,
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