import os
import pickle
import pandas as pd

i_dfs = []
for i_pkl_name in sorted(os.listdir("pkdb_pkls")):
    with open(os.path.join("pkdb_pkls", i_pkl_name), "rb") as f:
        i_dfs.append(pickle.loads(f.read()))

complete_dataframe = pd.concat(i_dfs)
