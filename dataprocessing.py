import pandas as pd  
import os  
from datetime import datetime
import streamlit as st  
import re  
from joblib import Parallel, delayed  
import zipfile
import os
from pathlib import Path 

#update FY tu dong  
def get_latest_budget_folder():
    root_path = r"Data_Link"
    
    if not os.path.exists(root_path):
        return None
    
    # Tạo list các năm FY có thể có (từ hiện tại ngược về quá khứ)
    current_year = int(datetime.now().strftime('%y'))
    possible_years = []
    for offset in range(0, 5):  # Kiểm tra 5 năm gần nhất
        fy_year = (current_year - offset) % 100  # FY26, FY25, FY24...
        possible_years.append(f"{fy_year:02d}")
    
    # Tìm thư mục BUDGET FYxx mới nhất có tồn tại
    for fy_year in possible_years:
        candidate_path = os.path.join(root_path, f"BUDGET FY{fy_year}")
        if os.path.exists(candidate_path) and os.path.isdir(candidate_path):
            return candidate_path
    
    return None

def extract_and_clean_zip_files(folder, clean_zip=True):  
    changed = False   
    for root, dirs, files in os.walk(folder):  
        for file in files:  
            if file.lower().endswith('.zip'):  
                zip_path = os.path.join(root, file)  
                try:  
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:  
                        zip_ref.extractall(root)  
                    if clean_zip:  
                        os.remove(zip_path)  
                    changed = True  
                    print(f"Đã giải nén và xóa: {zip_path}")  
                except Exception as e:  
                    print(f"Lỗi: {zip_path} - {e}")  
    if changed:  
        st.rerun()  
  

extract_and_clean_zip_files(r"\\10.147.32.1\MA_Div\Data_Link")

year = datetime.now().strftime('%y')
FOLDER_BUDGET = fr"\\10.147.32.1\MA_Div\Data_Link\BUDGET FY{year}"  
GROUP_PREFIX = {  
    'Assy':     [461, 462, 463, 464, 465, 469, 470, 474, 475, 476, 478, 480, 481, 484, 485, 486, 487, 488, 491, 492, 493, 494, 495],  
    'Control':  [312],  
    'Diecast':  [490],  
    'Process':  [468, 479, 482, 483, 489]  
}  
  
# --- GET FILES BY GROUP ---  
def get_files_by_group(folder_path, group_name, group_prefix=GROUP_PREFIX):
    
    # CHECK TỒN TẠI TRƯỚC KHI LISTDIR
    if not os.path.exists(folder_path):
        return []
    
    if not os.path.isdir(folder_path):
        return []
    
    if group_name not in group_prefix:
        return []
    
    try:
        all_files = [f for f in os.listdir(folder_path) if f.endswith('.xlsx')]
    except (FileNotFoundError, PermissionError, OSError) as e:
        return []
    
    # Lọc file theo prefix group
    prefixes = group_prefix[group_name]
    matched_files = []
    for pre in prefixes:
        patt = re.compile(rf'^{pre}\..*\.xlsx$', re.IGNORECASE)
        matched_files += [os.path.join(folder_path, f) for f in all_files if patt.match(f)]
    
    return matched_files 
  
# --- CLEAN DATA ---  
 
def clean_data(df):  
    try:  
        df = df.iloc[59:129, 3:15]  
        df.drop(columns=['Order date', 'Delivery date', 'Unnamed: 9', 'Judgement', 'Remark'], inplace=True)  
        df.rename(columns={'Unnamed: 14': 'Type'}, inplace=True)  
        df.rename(columns={'Accumulated Remain\n': 'Accumulated Remain'}, inplace=True)  
        df.rename(columns={'Amount (USD equivalent)\n': 'Amount (USD equivalent)'}, inplace=True)  
        return df  
    except Exception:  
        return pd.DataFrame()  

def clean_data_v2(df):  
    try:
        df = df.iloc[59:129, 3:15]
        df.drop(columns=[], inplace=True)
        df.rename(colums={}, inplace=True)
        df.rename(colums={}, imolace=True)
        df.rename(colums={}, inplace=True)
        return df
    except Exception:
        return pd.DataFrame()
# --- READ EXCEL FILES (FROM LIST) ---  
@st.cache_data 
def read_excel_files_from_list(file_paths, folder_ts):  
    month_names = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "JAN", "FEB", "MAR"]  
  
    def process_file(file_path, filename):  
        dfs = []  
        for month_name in month_names:  
            try:  
                df = pd.read_excel(file_path, sheet_name=month_name, header=9, engine='openpyxl')  
                if df.empty:  
                    continue  
                df = clean_data(df)  
                df['Month'] = month_name  
                df['Source File'] = filename  
                dfs.append(df)  
            except Exception:  
                continue  
        if dfs:  
            return pd.concat(dfs, ignore_index=True)  
        else:  
            return None  
  
    results = Parallel(n_jobs=10)(  
        delayed(process_file)(path, os.path.basename(path))  
        for path in file_paths  
    )  
    dfs = [df for df in results if df is not None]  
    if dfs:  
        return pd.concat(dfs, ignore_index=True)  
    else:  
        return pd.DataFrame()  
    
def summarize_variance_by_month(data):  
    month_order = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "JAN", "FEB", "MAR"]  
    data['Month'] = pd.Categorical(data['Month'], categories=month_order, ordered=True)  
  
    amount_summary = data.groupby('Month', observed=True)['Amount (USD equivalent)'].sum()  
    tmp = data.sort_values(['Month', 'Source File'])  
    first_accum = tmp.groupby(['Month', 'Source File'], observed=True)['Accumulated Remain'].first()  
    first_amount = tmp.groupby(['Month', 'Source File'], observed=True)['Amount (USD equivalent)'].first().fillna(0)  
    first_values_summary = (first_accum + first_amount).groupby('Month', observed=True).sum()  
  
    data['Xuất kho'] = data.apply(lambda row: row['Amount (USD equivalent)'] if pd.isna(row['Type']) else 0, axis=1)  
    data['BEC'] = data.apply(lambda row: row['Amount (USD equivalent)'] if not pd.isna(row['Type']) else 0, axis=1)  
  
    xuat_kho_summary = data.groupby('Month', observed=True)['Xuất kho'].sum()  
    bec_summary = data.groupby('Month', observed=True)['BEC'].sum()  
  
    summary_df = pd.DataFrame({  
        'AP': first_values_summary,  
        'Xuất kho': xuat_kho_summary,  
        'BEC': bec_summary,  
    })  
    return summary_df 

