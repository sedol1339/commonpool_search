from pathlib import Path
from tqdm import tqdm
import pandas as pd
import argparse
import subprocess
from pathlib import Path
import numpy as np
import gc
import re

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--folder',
        help="Folder with parquet files",
    )
    parser.add_argument(
        '--solr_path',
        help="Path to Solr directory",
        default="/opt/solr"
    )
    parser.add_argument(
        '--solr_core',
        help="Name of Solr collection",
        default="obelics"
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

            # processing file
            images = df.images.apply(lambda lst: ' '.join([x for x in lst if x is not None]))
            texts = df.texts.apply(lambda lst: ' '.join([x for x in lst if x is not None])).str.replace(r'\W', ' ').str.replace('\n', ' ')
            file_id = re.sub(r'[a-z-]+', '', filepath.stem)
            uid = pd.Series([file_id + str(x) for x in range(len(df))])
            df = pd.DataFrame({'id': uid, 'Text': texts, 'Url': images})

            # filtering file
            df = df[(df.Text.str.len() < 32767) & (df.Url.str.len() < 32767)]
            
            dfs.append(df)
            del df
        
        df_joint = pd.concat(dfs)
        df_joint.to_csv(csv_path, index=False)
        del df_joint

        print(csv_path)

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


