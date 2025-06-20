import streamlit as st
import pandas as pd
import re
import duckdb
from pathlib import Path
import os
import time

st.set_page_config(page_title="Hex Log Parser", layout="wide")
st.title("Hex Data Log Viewer with Timestamp Filtering (Local File Mode)")

filepath = st.text_input("Enter full path to your .txt log file (e.g., D:/logs/myfile.txt):")
exclude_keyword = st.text_input("Exclude blocks containing keyword (e.g., Ping or Debug):", value="Ping")

header_row = None

if filepath:
    filepath = Path(filepath)
    if not filepath.exists():
        st.error("File not found. Please check the path.")
    else:
        file_size = os.path.getsize(filepath)
        with st.spinner("Reading file line by line and excluding specified keywords..."):
            raw_blocks = []

            progress_bar = st.progress(0)
            status_text = st.empty()
            bytes_read = 0
            match_count = 0
            buffer = []

            with open(filepath, "r", encoding="utf-8", errors='ignore') as f:
                first_line = f.readline()
                if "TimeStamp" in first_line:
                    f.seek(0)  # Valid header, reprocess from start
                else:
                    st.warning("First line does not contain 'TimeStamp'. Skipping as non-log content.")

                for line_num, line in enumerate(f, 2):
                    line_bytes = len(line.encode('utf-8', errors='ignore'))
                    bytes_read += line_bytes
                    progress_ratio = bytes_read / file_size if file_size > 0 else 0
                    progress = min(100, int(progress_ratio * 100))
                    if line_num % 500 == 0:
                        progress_bar.progress(progress)
                        status_text.text(f"Processing line {line_num:,}... {progress}% | Matches found: {match_count}")

                    is_timestamp = "TimeStamp" in line

                    if is_timestamp:
                        if buffer:
                            joined_block = '\n'.join(buffer)
                            if not re.search(fr"\b{re.escape(exclude_keyword)}\b", joined_block, re.IGNORECASE):
                                raw_blocks.append(buffer[:])
                                match_count += 1
                        buffer = [line.strip()]  # start new block with timestamp line only
                    else:
                        if buffer and buffer[0].startswith("TimeStamp"):
                            buffer.append(line.strip())

                if buffer:
                    joined_block = '\n'.join(buffer)
                    if not re.search(fr"\b{re.escape(exclude_keyword)}\b", joined_block, re.IGNORECASE):
                        raw_blocks.append(buffer[:])
                        match_count += 1

            progress_bar.empty()
            status_text.text(f"Parsing complete. Matches found: {match_count}")

        parsed_data = []
        if header_row:
            parsed_data.append(header_row)

        for block in raw_blocks:
            for line in block:
                parsed_data.append(re.split(r' {2,}|\t+', line.strip()))

        original_df = pd.DataFrame(parsed_data, dtype=object)
        original_df = original_df.loc[(original_df != '').any(axis=1)]
        original_df.index = [str(i+1) for i in range(len(original_df))]

        if "col36" in original_df.columns:
            filtered_df = original_df[original_df["col36"].notna() & (original_df["col36"] != '')]
            st.subheader("Filtered Rows with col36 Present")
            st.dataframe(filtered_df)
        else:
            st.info("No col36 present in parsed data.")

        st.subheader("Original Parsed Data Table (Raw 4-line Format)")
        st.dataframe(original_df)

        csv_original = original_df.to_csv(index=False)
        st.download_button("Download original 4-line CSV", csv_original, "parsed_output_4row.csv")

        row_list = original_df.values.tolist()
        two_line_data = []
        for i in range(0, len(row_list), 6):
            if i + 5 < len(row_list):
                combined1 = row_list[i] + row_list[i+3]
                combined2 = row_list[i+1] + row_list[i+4]
                two_line_data.append(combined1)
                two_line_data.append(combined2)

        if two_line_data:
            max_two_cols = max(len(row) for row in two_line_data)
            two_line_df = pd.DataFrame(two_line_data, columns=[f"col{i}" for i in range(max_two_cols)])
            two_line_df = two_line_df.loc[(two_line_df != '').any(axis=1)]
            two_line_df.index = [str(i+1) for i in range(len(two_line_df))]

            st.subheader("Parsed Data Table (2-row Format per Block)")
            st.dataframe(two_line_df)

            csv_two = two_line_df.to_csv(index=False)
            st.download_button("Download parsed CSV (2-row format)", csv_two, "parsed_output_2row.csv")
        else:
            st.info("No valid blocks found for 2-row parsing.")
