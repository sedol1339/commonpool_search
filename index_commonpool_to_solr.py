from pathlib import Path
from tqdm import tqdm
import pandas as pd
import argparse
import subprocess
from pathlib import Path
import numpy as np
import gc

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--folder',
        help="Folder with parquet files",
    )
    parser.add_argument(
        '--min_width',
        help="Skip all images with width less than specified",
        type=int,
        default=0
    )
    parser.add_argument(
        '--min_height',
        help="Skip all images with height less than specified",
        type=int,
        default=0
    )
    parser.add_argument(
        '--solr_path',
        help="Path to Solr directory",
        default="/opt/solr"
    )
    parser.add_argument(
        '--solr_core',
        help="Name of Solr collection",
        default="commonpool"
    )
    parser.add_argument(
        '--remove_parquet_on_success',
        help="Remove .parquet (symlinks and targets) on successful indexing",
        action="store_true"
    )
    parser.add_argument(
        '--shard_size',
        help="Post N parquet files per one Solr post",
        type=int,
        default=1
    )
    # parser.add_argument(
    #     '--clip_scores',
    #     help="add {t} to description if clip L/14 similarity score for image-text pair is higher than {t} for {t} in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]",
    #     action="store_true"
    # )
    args = parser.parse_args()

    filepaths = list(Path(args.folder).glob('*.parquet'))
    filepaths_groups = [filepaths[i:i+args.shard_size] for i in range(0, len(filepaths), args.shard_size)]
    for filepaths_group in tqdm(filepaths_groups):

        gc.collect()
        gc.collect()
        
        csv_path = filepaths_group[0].parent / (filepaths_group[0].stem + '.csv')
        csv_path.unlink(missing_ok=True)

        dfs = []

        for filepath in filepaths_group:
        
            # specifying tmp paths and cleaning
            
            # reading parquet
            df = pd.read_parquet(filepath, engine='pyarrow')
            orig_len = len(df)
    
            # filtering data
            df = df[df.original_width >= args.min_width]
            df = df[df.original_height >= args.min_height]
            df = df[(df.text.str.len() < 1000) & (df.url.str.len() < 32767)]
    
            # adding clip scores
            # if args.clip_scores:
            #     text_col = df.columns.get_loc('text')
            #     for threshold in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
            #         suffix = np.full(len(df), "", dtype=object)
            #         suffix[df.clip_l14_similarity_score > threshold] = str(threshold)
            #         df.text = df.text + ' ' + pd.Series(suffix)
            
            # saving required columns to csv
            df = df[['uid', 'text', 'url']] \
                .rename(columns={'uid': 'id', 'text': 'Text', 'url': 'Url'})
            print(f'{filepath.name}: left {len(df)} of {orig_len} rows ({len(df)/orig_len*100:.1f}%)')

            dfs.append(df)
            del df
        
        df_joint = pd.concat(dfs)
        df_joint.to_csv(csv_path)
        del df_joint

        cmd = f"{args.solr_path}/bin/post -c {args.solr_core} -commit no {str(csv_path)}"
        print(f'Running command: {cmd}')

        result = subprocess.run(cmd.split()) #, stdout=subprocess.DEVNULL)

        if result.returncode == 0:
            # success, removing files
            if args.remove_parquet_on_success:
                # removing csv
                csv_path.unlink()
                for filepath in filepaths_group:
                    # removing symlink target
                    Path(filepath).resolve().unlink()
                    # removing symlink (if this was a symlink)
                    Path(filepath).unlink(missing_ok=True)
        else:
            #some error
            raise Exception(f'Command returned non-zero code {result.returncode}')


