# import pandas as pd
# from pathlib import Path

# # 1. Define your base directory using a raw string (r"...") for Windows paths
# base_path = Path(r"C:\Users\ADITYA\Downloads\SPY")

# # 2. Iterate through every item in the base directory
# for year_folder in base_path.iterdir():
    
#     # Check if the item is a directory and named as a year (e.g., "2017")
#     if year_folder.is_dir() and year_folder.name.isdigit():
#         print(f"Processing year: {year_folder.name}...")
        
#         yearly_dfs = []
        
#         # 3. Find all files starting with 'spy_eod_' inside the year folder
#         for file_path in year_folder.glob("spy_eod_*"):
#             try:
#                 # Read the file. (Assumes they are comma-separated. 
#                 # If they are tab-separated, add sep='\t' to read_csv)
#                 df = pd.read_csv(file_path,low_memory=False)
#                 yearly_dfs.append(df)
#             except Exception as e:
#                 print(f"  -> Error reading {file_path.name}: {e}")
                
#         # 4. If files were successfully read, combine and convert them
#         # 4. If files were successfully read, combine and convert them
#         if yearly_dfs:
#             # Concatenate all 12 months into a single DataFrame for the year
#             combined_year_df = pd.concat(yearly_dfs, ignore_index=True)
            
#             # --- NEW DATA CLEANING STEP ---
#             # Loop through every column in the combined dataframe
#             for col in combined_year_df.columns:
#                 # If Pandas flagged the column as 'object' (mixed types/strings)
#                 if combined_year_df[col].dtype == 'object':
#                     try:
#                         # Try to force the column to be numeric (floats).
#                         # errors='coerce' turns unparseable text like " " or "-" into NaN
#                         combined_year_df[col] = pd.to_numeric(combined_year_df[col], errors='coerce')
#                     except Exception:
#                         # If it completely fails (e.g., the Option Symbol column), 
#                         # force everything in that column to be a uniform string.
#                         combined_year_df[col] = combined_year_df[col].astype(str)
#             # ------------------------------
            
#             # Define the output Parquet filename
#             output_file = base_path / f"SPY_{year_folder.name}.parquet"
            
#             # 5. Save to Parquet format using pyarrow
#             combined_year_df.to_parquet(output_file, engine='pyarrow', index=False)
#             print(f"  -> Successfully saved: {output_file.name}")

# print("All years have been processed and converted to Parquet!")



# import pandas as pd
# from pathlib import Path

# # 1. Define the path to ONE of your new Parquet files to test
# # Change 'SPY_2017.parquet' to whichever year you want to inspect
# file_path = Path(r"C:\Users\ADITYA\Downloads\SPY\SPY_2017.parquet")

# def check_parquet_data(path):
#     print(f"--- Loading Data from {path.name} ---\n")
    
#     try:
#         # Load the Parquet file
#         df = pd.read_parquet(path)
#     except Exception as e:
#         print(f"Failed to load file: {e}")
#         return

#     # 2. Basic Shape and Size
#     print("1. DATASET SIZE:")
#     print(f"Total Rows: {df.shape[0]:,}")
#     print(f"Total Columns: {df.shape[1]}\n")

#     # 3. Data Types
#     print("2. DATA TYPES (Ensure prices/IV are float64):")
#     print(df.dtypes, "\n")

#     # 4. Missing Values Check
#     # This shows how many blanks/NaNs exist in each column
#     print("3. MISSING VALUES (Null/NaN count per column):")
#     null_counts = df.isnull().sum()
#     print(null_counts[null_counts > 0]) # Only print columns that actually have missing data
#     print("\n")

#     # 5. Summary Statistics for Numeric Columns
#     # This helps you spot weird outliers (e.g., negative prices)
#     print("4. SUMMARY STATISTICS (Prices & Volume):")
#     # Adjust this list based on your actual column names
#     cols_to_check = ['C_LAST', 'P_LAST', 'C_IV', 'P_IV'] 
    
#     # Filter the list to only include columns that actually exist in the dataframe
#     existing_cols = [col for col in cols_to_check if col in df.columns]
    
#     if existing_cols:
#         print(df[existing_cols].describe())
#     else:
#         print("Standard price/IV columns not found. Printing general stats:")
#         print(df.describe())
#     print("\n")

#     # 6. Data Snapshot
#     print("5. DATA SNAPSHOT (First 5 rows):")
#     print(df.head())
#     print("Column Names:")
#     print(df.columns.tolist())

# # Run the check
# check_parquet_data(file_path)


import pandas as pd
from pathlib import Path

# 1. Define your base directory
base_path = Path(r"C:\Users\ADITYA\Downloads\SPY")

def combine_and_clean_parquets(directory):
    print("Starting the combination process...")
    
    # List to hold all the cleaned yearly dataframes
    all_dataframes = []
    
    # 2. Find all the yearly Parquet files we created
    # This assumes they were named like SPY_2010.parquet, SPY_2011.parquet, etc.
    parquet_files = list(directory.glob("SPY_20*.parquet"))
    
    if not parquet_files:
        print("No yearly Parquet files found. Check your directory path.")
        return

    # 3. Loop through each file, clean the columns, sort, and store it
    for file in parquet_files:
        print(f"Loading and cleaning: {file.name}...")
        df = pd.read_parquet(file)
        
        # CLEANING STEP: Remove '[' and ']', then strip extra spaces from both ends
        df.columns = df.columns.str.replace('[', '', regex=False)
        df.columns = df.columns.str.replace(']', '', regex=False)
        df.columns = df.columns.str.strip()
        
        # Sort each yearly dataframe individually (uses much less memory)
        df = df.sort_values(by=['QUOTE_UNIXTIME'])
        
        all_dataframes.append(df)
        
    # 4. Combine all the cleaned and already-sorted dataframes into one master dataframe
    print("\nConcatenating all years into a single dataset. This might take a moment...")
    master_df = pd.concat(all_dataframes, ignore_index=True)
    
    print("Data is already sorted chronologically (each year was sorted individually).")
    
    # 5. Save the master dataframe
    output_filename = directory / "SPY_ALL_YEARS_MASTER.parquet"
    print(f"\nSaving master file to: {output_filename.name}")
    
    # Save as Parquet. Using engine='pyarrow'
    master_df.to_parquet(output_filename, engine='pyarrow', index=False)
    
    print(f"Success! Master file created with {master_df.shape[0]:,} rows and {master_df.shape[1]} columns.")
    
    # Show the newly cleaned columns
    print("\nCleaned Column Names:")
    print(master_df.columns.tolist())

# Run the script
combine_and_clean_parquets(base_path)