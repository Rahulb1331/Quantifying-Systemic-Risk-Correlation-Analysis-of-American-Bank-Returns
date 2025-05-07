import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
import functools

# Helper to convert Google Drive links to direct download URLs
@st.cache_data(show_spinner=False)
def gdrive_to_direct_link(url):
    file_id = url.split("/d/")[1].split("/")[0]
    return f"https://drive.google.com/uc?export=download&id={file_id}"

# Dataset download links
macro_links = {
    "10YMinus3MTreasurySpread": "https://drive.google.com/file/d/1LnMCD68ytKhp6qwa0gF4VfL0diw0eGxs/view?usp=drive_link",
    "10YInflation": "https://drive.google.com/file/d/1msVZaY-EjBejN48udF7bWI235eP1H7Yw/view?usp=drive_link",
    "EFFR": "https://drive.google.com/file/d/1gU9pj9y-HZ4RwPKn4kmUDdwiflxdY1hi/view?usp=drive_link",
    "ICE_BOFA": "https://drive.google.com/file/d/1xGAx5l927t-90f8wrtgTquz9Rwl-3ffc/view?usp=drive_link",
    "RIFSPPFAAD07NB": "https://drive.google.com/file/d/1bTr0te7VVZm242zZX3eaE7UXfDlUxbet/view?usp=drive_link",
    "VIXCLS": "https://drive.google.com/file/d/1wDu78j344cxHXP4cY0Ol_4n_9nJI00wj/view?usp=drive_link",
}

# Helper to convert Google Drive file URLs to direct download links
@st.cache_data
def gdrive_to_direct_link(url: str) -> str:
    file_id = url.split("/d/")[1].split("/")[0]
    return f"https://drive.google.com/uc?export=download&id={file_id}"

# 2. Load raw macro DataFrames
@st.cache_data
def load_raw_macros(links: dict) -> dict:
    dfs = {}
    for name, url in links.items():
        direct = gdrive_to_direct_link(url)
        df = pd.read_csv(direct)
        # Normalize date column
        date_col = [c for c in df.columns if 'date' in c.lower()][0]
        df = df.rename(columns={date_col: 'Date'})
        df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format=True)
        # Rename data column to the key
        value_col = [c for c in df.columns if c != 'Date'][0]
        df = df.rename(columns={value_col: name})
        dfs[name] = df[['Date', name]]
    return dfs
    
# 3. Merge all macro DataFrames
@st.cache_data
def merge_macros(links: dict) -> pd.DataFrame:
    dfs = load_raw_macros(links)
    macro_df = functools.reduce(lambda left, right: pd.merge(left, right, on='Date', how='outer'),
                                dfs.values())
    macro_df = macro_df.sort_values('Date').reset_index(drop=True)
    return macro_df

# 4. Transform macro series to stationary z-scores or differences
@st.cache_data
def transform_macros(macro_df: pd.DataFrame) -> pd.DataFrame:
    df = macro_df.copy()
    # 4a. VIX: first diff and z-score
    df['dVIXCLS'] = df['VIXCLS'].diff()
    df['zVIXCLS'] = (df['dVIXCLS'] - df['dVIXCLS'].mean()) / df['dVIXCLS'].std()
    # 4b. EFFR: first diff and z-score
    df['dEFFR'] = df['EFFR'].diff()
    df['zEFFR'] = (df['dEFFR'] - df['dEFFR'].mean()) / df['dEFFR'].std()
    # 4c. Treasury slope: level z-score
    df['z10Y3M'] = (df['10YMinus3MTreasurySpread'] -
                    df['10YMinus3MTreasurySpread'].mean()) / df['10YMinus3MTreasurySpread'].std()
    # 4d. High-Yield OAS: first diff and z-score
    df['dICE_BOFA'] = df['ICE_BOFA'].diff()
    df['zICE_BOFA'] = (df['dICE_BOFA'] - df['dICE_BOFA'].mean()) / df['dICE_BOFA'].std()
    # 4e. Commercial Paper: first diff and z-score
    df['dRIF'] = df['RIFSPPFAAD07NB'].diff()
    df['zRIF'] = (df['dRIF'] - df['dRIF'].mean()) / df['dRIF'].std()
    # 4f. Breakeven inflation: first diff and z-score
    df['d10YInfl'] = df['10YInflation'].diff()
    df['z10YInfl'] = (df['d10YInfl'] - df['d10YInfl'].mean()) / df['d10YInfl'].std()
    return df

# 5. Merge banks and macros into full panel
@st.cache_data
def build_full_panel(df_banks: pd.DataFrame, links: dict) -> pd.DataFrame:
    macro_raw = merge_macros(links)
    macro_trans = transform_macros(macro_raw)
    full = pd.merge(df_banks, macro_trans, on='Date', how='left')
    return full

banks_dataset_link = {
    "JPM": "https://drive.google.com/file/d/1OggspqOFXXbGC9C_VC1FlOrJufAPd8jE/view?usp=sharing",
    "BAC": "https://drive.google.com/file/d/146JFCXYlJC5ek-_OWYKPIzoq6xiQEOYd/view?usp=sharing",
    "C": "https://drive.google.com/file/d/1IbQFcJXobNiWRpCP7AfMhvTwQ_PBX3ib/view?usp=drive_link",
    "GS": "https://drive.google.com/file/d/1PyNbQ-AnpkMJVYPfLzqcuQrXFMBAnB1Q/view?usp=drive_link",
    "MS": "https://drive.google.com/file/d/13WxDcl2bsDYJfY4-k0-3Vw1QhgraMw7W/view?usp=drive_link",
    "WFC": "https://drive.google.com/file/d/1NOWT_1KU0NRQ-mTS1PYrlwPi08joNxpX/view?usp=drive_link",
    "USB": "https://drive.google.com/file/d/1uXTAYO7sR4HPdqJxyH14U26Fi6XyCylz/view?usp=drive_link",
    "PNC": "https://drive.google.com/file/d/10tq02KNXPB_MX5-4dFxXRfJPgzqwKld2/view?usp=drive_link",
    "TFC": "https://drive.google.com/file/d/1RYiWJI3-UC2x3QGeovm0F25BmoREhxAg/view?usp=drive_link",
    "BK": "https://drive.google.com/file/d/1nJ_r064eJ8Beqox2bIzl1zFIR3spEZj8/view?usp=drive_link",
    "SCHW": "https://drive.google.com/file/d/19qJaY4mxVoL73n5cytlYwsGnP_uJvNti/view?usp=drive_link",
    "COF": "https://drive.google.com/file/d/1T3jne2Nb829_i-wo0bvP4zejmzNTbROR/view?usp=drive_link",
    "STT": "https://drive.google.com/file/d/1T9Ew2Bz1XAHuunzV6F6Yb7rPKY7WfGhU/view?usp=drive_link"
}

# Download and load into DataFrames
@st.cache_data(show_spinner=False)
def load_raw_dfs(banks_dataset_link: dict) -> dict:
    dfs = {}
    for name, url in banks_dataset_link.items():
        direct_url = gdrive_to_direct_link(url)
        dfs[name] = pd.read_csv(direct_url)
    return dfs


bank_tickers = list(banks_dataset_link.keys())

# 3. Cache per-bank cleaning
@st.cache_data(show_spinner=True)
def clean_bank_df(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format=True)
    def parse_vol(s):
        s = str(s).strip().upper()
        if s.endswith("K"):
            return float(s[:-1].replace(",", "")) * 1e3
        if s.endswith("M"):
            return float(s[:-1].replace(",", "")) * 1e6
        if s.endswith("B"):
            return float(s[:-1].replace(",", "")) * 1e9
        return float(s.replace(",", ""))
    df[f'Volume_{ticker}'] = df['Vol.'].apply(parse_vol)
    df[f'Change_{ticker}'] = (
        df['Change %']
          .str.rstrip('%')
          .astype(float) / 100.0
    )
    df.drop(columns=['Vol.', 'Change %'], inplace=True)
    rename_map = {
        'Price': f'Price_{ticker}',
        'Open':  f'Open_{ticker}',
        'High':  f'High_{ticker}',
        'Low':   f'Low_{ticker}'
    }
    df.rename(columns=rename_map, inplace=True)
    cols = ['Date'] + [c for c in df.columns if c.endswith(f'_{ticker}')]
    return df[cols]


# 4. Cache the merge of all banks
@st.cache_data(show_spinner=True)
def load_and_merge_all_banks(banks_dataset_link: dict, bank_tickers: list) -> pd.DataFrame:
    dfs = load_raw_dfs(banks_dataset_link)
    cleaned = {t: clean_bank_df(dfs[t], t) for t in bank_tickers}
    merged = cleaned[bank_tickers[0]]
    for t in bank_tickers[1:]:
        merged = merged.merge(cleaned[t], on='Date', how='outer')
    merged.sort_values('Date', inplace=True)
    merged.reset_index(drop=True, inplace=True)
    return merged

df_merged = load_and_merge_all_banks(banks_dataset_link, bank_tickers)
st.success(f"Merged {len(bank_tickers)} banks: {df_merged.shape[0]} rows × {df_merged.shape[1]} cols")
st.dataframe(df_merged.head())



# Usage: assume df_banks exists from your bank-merge code
df_full = build_full_panel(df_merged, macro_links)
st.success(f"Full panel: {df_full.shape[0]} rows × {df_full.shape[1]} cols")
st.dataframe(df_full.head())
