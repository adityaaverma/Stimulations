import pandas as pd
from pathlib import Path
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("OptionsDX_Compiler")

def compile_optionsdx(raw_base_dir: str, output_parquet_path: str):
    """
    Recursively scans the Desktop/SPY folder, reads the .txt files,
    cleans headers, filters DTE, and outputs a single Parquet file.
    """
    # Use expanduser to automatically resolve '~' to your actual User directory
    base_path = Path(raw_base_dir).expanduser()
    
    # We are specifically looking for the .txt files you mentioned
    file_list = list(base_path.rglob("*.txt"))
    
    if not file_list:
        logger.error(f"No TXT files found in {base_path}. Check the folder name and path.")
        return

    logger.info(f"Found {len(file_list)} .txt files. Processing...")

    processed_chunks = []
    
    # Only keeping columns necessary for the VolTrading Engine to save RAM
    cols_to_keep = [
        'quote_date', 'expire_date', 'dte', 'underlying_last', 'strike',
        'c_bid', 'c_ask', 'c_last', 'c_iv', 'c_volume', 'c_delta', 'c_gamma', 'c_vega', 'c_theta',
        'p_bid', 'p_ask', 'p_last', 'p_iv', 'p_volume', 'p_delta', 'p_gamma', 'p_vega', 'p_theta'
    ]

    for file_path in file_list:
        try:
            # OptionsDX .txt files are standard comma-separated files
            df = pd.read_csv(file_path, low_memory=False)
            
            # Clean OptionsDX Headers (removes brackets and spaces)
            df.columns = (
                df.columns.str.replace('[', '', regex=False)
                          .str.replace(']', '', regex=False)
                          .str.strip()
                          .str.lower()
            )
            
            # Ensure we only extract columns that actually exist
            existing_cols = [c for c in cols_to_keep if c in df.columns]
            df = df[existing_cols]
            
            # Filter 1: Apply DTE constraints (5 to 120 days)
            # if 'dte' in df.columns:
            #     df['dte'] = pd.to_numeric(df['dte'], errors='coerce')
            #     df = df[(df['dte'] >= 5) & (df['dte'] <= 120)]
            
            # Filter 2: Drop dead contracts (where bid is 0)
            # if 'c_bid' in df.columns and 'p_bid' in df.columns:
            #     df['c_bid'] = pd.to_numeric(df['c_bid'], errors='coerce').fillna(0)
            #     df['p_bid'] = pd.to_numeric(df['p_bid'], errors='coerce').fillna(0)
            #     df = df[(df['c_bid'] > 0) | (df['p_bid'] > 0)]
            
            if not df.empty:
                processed_chunks.append(df)
                
        except Exception as e:
            logger.warning(f"Could not process file {file_path.name}: {e}")

    if not processed_chunks:
        logger.error("No data remained after filtering. Script stopping.")
        return

    # Concatenate all months/years into one master DataFrame
    logger.info("Concatenating all files into Master DataFrame...")
    master_df = pd.concat(processed_chunks, ignore_index=True)
    
    # Ensure datetime formatting for your engine's MultiIndex
    master_df['quote_date'] = pd.to_datetime(master_df['quote_date'])
    master_df['expire_date'] = pd.to_datetime(master_df['expire_date'])
    
    # Sort for sequential event-driven backtesting
    logger.info("Sorting data chronologically...")
    master_df = master_df.sort_values(['quote_date', 'strike', 'expire_date']).reset_index(drop=True)
    
    # Export to Parquet
    os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
    logger.info(f"Saving {len(master_df):,} rows to {output_parquet_path}...")
    master_df.to_parquet(output_parquet_path, engine='pyarrow', index=False)
    
    logger.info("Compilation Complete! Move the parquet file to your project's data directory.")

if __name__ == "__main__":
    # Pointing to the SPY folder on your OneDrive Desktop
    RAW_DATA_FOLDER = "C:\\Users\\ADITYA\\OneDrive\\Desktop\\SPY" 
    
    # Saving the final Parquet file directly to your OneDrive Desktop
    OUTPUT_PARQUET = "C:\\Users\\ADITYA\\OneDrive\\Desktop\\full_chain.parquet"
    
    compile_optionsdx(RAW_DATA_FOLDER, OUTPUT_PARQUET)