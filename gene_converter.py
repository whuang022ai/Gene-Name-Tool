import biomart
import pandas as pd
from io import StringIO
import os
import numpy as np
from itertools import chain
name_ensemblid2symbol="_ensemblid2symbol"

def fetch_dataset_from_file(dataset_name, symbol_meta_name):
    target_fname = f"{dataset_name}{name_ensemblid2symbol}.pkl"
    if os.path.isfile(target_fname):
        df = pd.read_pickle(target_fname)
        df2 = df.reset_index()
        df2.set_index("gene_symbol",inplace=True)
        return df,df2, target_fname
    else:
        return fetch_dataset_from_url(dataset_name=dataset_name, symbol_meta_name=symbol_meta_name)

def fetch_dataset_from_url(dataset_name,symbol_meta_name,server_url="http://www.ensembl.org/biomart"):
    server = biomart.BiomartServer( server_url )
    mart = server.datasets[dataset_name]  
    attributes = ['ensembl_gene_id', symbol_meta_name]
    response = mart.search({'attributes': attributes})
    data = response.raw.data.decode('utf-8')
    data_set=StringIO(data)
    df = pd.read_csv(data_set, sep="\t", lineterminator='\n',header=None)
    df.columns=attributes
    df.set_index("ensembl_gene_id",inplace=True)
    df.rename(columns={symbol_meta_name: 'gene_symbol'},inplace=True)
    df.to_pickle(dataset_name+name_ensemblid2symbol+'.pkl')

    return df,dataset_name+name_ensemblid2symbol+'.pkl'

def fetch_mm_dataset():
    return fetch_dataset_from_file("mmusculus_gene_ensembl", "mgi_symbol")

def fetch_hg_dataset():
    return fetch_dataset_from_file("hsapiens_gene_ensembl", "hgnc_symbol")
    
def gene_ensembl_lines_to_symbol(lines,convert_df,case_sensitive,unmatch_placeholder=np.nan,qc_file_name=None):
    
    lines = lines.split('\n')
    lines = [line.strip() for line in lines]
    filter_df = pd.DataFrame(columns=convert_df.columns)
    frames = []
    total_input_num=len(lines)
    qc_output_NaN_num=0 # empty output line number
    qc_input_empty_line=0
    for line in lines:
        if not line.strip() or line in ['\n', '\r\n']:
            qc_input_empty_line+=1
        if not case_sensitive:
            line =line.lower()
            if line in convert_df.index.str.lower():
                ix=convert_df.index.str.lower().get_loc(line)
                subset=convert_df.iloc[ix]
                if len(subset)==1:
                    i=subset.item()
                else:
                    i_s=subset.values.tolist()
                    
                    i_s = list(chain.from_iterable(i_s))
                    i = ','.join(i_s)
                row = pd.DataFrame([i], columns=convert_df.columns, index=[line])
                frames.append(row)
            else:
                empty_row = pd.DataFrame([[unmatch_placeholder] * len(convert_df.columns)], columns=convert_df.columns, index=[line])
                qc_output_NaN_num+=1
                frames.append(empty_row)
        else:

            if line in convert_df.index:
                subset=convert_df.loc[[line]]
                if len(subset)==1:
                    i=subset.values.tolist()[0]
                else:
                    i_s=subset.values.tolist()
                    i_s = list(chain.from_iterable(i_s))
                    i = ','.join(i_s)
                row = pd.DataFrame([i], columns=convert_df.columns, index=[line])
                frames.append(row)
            else:
                empty_row = pd.DataFrame([[unmatch_placeholder] * len(convert_df.columns)], columns=convert_df.columns, index=[line])
                qc_output_NaN_num+=1
                frames.append(empty_row)
    filter_df = pd.concat(frames)
    qc_summary =\
    f"""
    Gene Name Tool v0.0.0
    ---------------------------
    Total lines of input genes: {total_input_num}
    Empty lines of input genes: {qc_input_empty_line} , {qc_input_empty_line/total_input_num*100:.2f} %
    Unknown lines of output genes (NaN or no match): {qc_output_NaN_num} , {qc_output_NaN_num/total_input_num*100:.2f} %
    Success conversion rate:  {100 - qc_output_NaN_num/total_input_num*100:.2f} %
    ---------------------------
    """
    if qc_file_name:
        with open(qc_file_name, 'w') as f:
            f.write(qc_summary)
    print(qc_summary)
    unknow_ensembl_id = set(lines) - set(convert_df.index)
    return filter_df,unknow_ensembl_id
