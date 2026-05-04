# Fetch data 

import pandas as pd
from datetime import datetime
import uuid
from pathlib import Path
import os
import hashlib

def read_statements (file_path):
    """ Reads a single CSV file and adds audit metadata and UUIDs.
    Return: Dataframe (an empty DataFrame if the file is empty)."""

    file = Path(file_path)

    empty_df = pd.DataFrame()  # Define an empty DataFrame to return in case of issues
    
    try:
        # Check if file is empty (size == 0 bytes)
        if os.path.getsize(file) == 0:
            print(f"Skipping empty file: {file}")
            return empty_df  # Return empty DataFrame for consistency            

        df = pd.read_csv(file)

        # Add Metadata & UUIDs
        # Using .assign is cleaner and often faster for multiple columns
        df = df.assign(
            source_name=file.stem,
            load_timestamp=datetime.now(),
            transaction_id=[uuid.uuid4().hex for _ in range(len(df))]
        )
       
        # Handle case where file has headers but no rows
        if df.empty:
            print(f"Skipping file with no data rows: {file}")
            return empty_df  # Return empty DataFrame for consistency

        return df

    except pd.errors.EmptyDataError:
        print(f"Skipping invalid/empty CSV: {file}")
    except pd.errors.ParserError as e:
        print(f"Parsing error in {file}: {e}")
    except Exception as e:
        print(f"Unexpected error reading {file}: {e}")

    return empty_df


def get_file_hash(filepath):
    """Generates a unique ID for a file based on its content."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

log_file = "data/processed_log.txt"
def log_processed_file(filepath, file_hash, row_count):
    """Updates the log with a timestamp, filename, hash, and row count."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_name = os.path.basename(filepath)
    
    # Write header if the file doesn't exist
    write_header = not os.path.exists(log_file)
    
    with open(log_file, 'a') as f:
        if write_header:
            f.write("timestamp,file_name,hash,row_count\n")
        f.write(f"{timestamp},{file_name},{file_hash},{row_count}\n")

def get_processed_files():
    """Reads the log and returns a set of hashes for quick checking."""
    if not os.path.exists(log_file):
        return set()
    
    # Use pandas to read the CSV log and extract the 'hash' column
    try:
        log_df = pd.read_csv(log_file)
        return set(log_df['hash'].astype(str).tolist())
    except Exception:
        # Fallback if the file is empty or formatted incorrectly
        return set()

def ingest_data(file_path, processed_hashes, transformer, raw_path):
    """ Read a single file, log processed files, and return a combined raw file in `parquet` format.
    This function will only process new files that haven't been processed before. """

    file_hash = get_file_hash(file_path)

    if file_hash not in processed_hashes:
        print(f"Processing new file: {file_path}")
        df = read_statements(file_path).pipe(transformer)
        if not df.empty:
            log_processed_file(file_path, file_hash, len(df))

            # Incremental Ingestion:
            # Loading existing raw data (if it exists) and appending new data to it
            if os.path.exists(raw_path):
                existing_raw_df = pd.read_parquet(raw_path)
                full_history_df = pd.concat([existing_raw_df, df], ignore_index=True)
            else:
                full_history_df = df

            full_history_df.to_parquet(raw_path, engine='pyarrow', index=False)
            return full_history_df

    return pd.DataFrame()