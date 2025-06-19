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

if filepath:
    filepath = Path(filepath)
    if not filepath.exists():
        st.error("File not found. Please check the path.")
    else:
        file_size = os.path.getsize(filepath)
        st.info("Reading file line by line to avoid memory error and exclude ping events...")
        parsed_data = []

        progress_bar = st.progress(0)
        status_text = st.empty()
        table_placeholder = st.empty()
        bytes_read = 0
        match_count = 0
        buffer = []

        output_df = pd.DataFrame()
        display_placeholder = st.empty()

        with open(filepath, "r", encoding="utf-8", errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line_bytes = len(line.encode('utf-8', errors='ignore'))
                bytes_read += line_bytes
                progress_ratio = bytes_read / file_size if file_size > 0 else 0
                progress = min(100, int(progress_ratio * 100))
                if line_num % 500 == 0:
                    progress_bar.progress(progress)
                    status_text.text(f"Processing line {line_num:,}... {progress}% | Matches found: {match_count}")

                if re.match(r"^\d+\.\d+?s\s+", line):
                    if buffer:
                        joined_block = ''.join(buffer)
                        if not re.search(r"\bPing\b", joined_block, re.IGNORECASE):
                            block_rows = [re.split(r'\s{2,}', block_line.strip()) for block_line in buffer if block_line.strip() and any(re.split(r'\s{2,}', block_line.strip()))]
                            parsed_data.extend(block_rows)
                            match_count += 1

                            temp_df = pd.DataFrame(block_rows)
                            output_df = pd.concat([output_df, temp_df], ignore_index=True)
                            display_placeholder.dataframe(output_df)
                    buffer = [line.strip()]
                else:
                    buffer.append(line.strip())

            if buffer:
                joined_block = ''.join(buffer)
                if not re.search(r"\bPing\b", joined_block, re.IGNORECASE):
                    block_rows = [re.split(r'\s{2,}', block_line.strip()) for block_line in buffer if block_line.strip() and any(re.split(r'\s{2,}', block_line.strip()))]
                    parsed_data.extend(block_rows)
                    match_count += 1

                    temp_df = pd.DataFrame(block_rows)
                    output_df = pd.concat([output_df, temp_df], ignore_index=True)
                    display_placeholder.dataframe(output_df)

        progress_bar.empty()
        status_text.text(f"Parsing complete. Matches found: {match_count}")

        df = output_df.copy()
        df = df.loc[(df != '').any(axis=1)]  # Remove entirely empty rows
        df.index = [str(i+1) for i in range(len(df))]  # row names as 1, 2, 3, ...
        df.columns = [f"col{i}" for i in range(df.shape[1])]

        st.subheader("Parsed Data Table")
        columns_to_show = st.multiselect("Select columns to display:", df.columns.tolist(), default=df.columns.tolist())
        st.dataframe(df[columns_to_show])

        st.subheader("Keyword Filter")
        keyword = st.text_input("Filter rows that contain keyword (e.g., 0X1 or ACK):")
        if keyword:
            mask = df.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)
            st.write(f"Filtered Rows containing '{keyword}':")
            st.dataframe(df[mask][columns_to_show])

            csv = df[mask][columns_to_show].to_csv(index=False)
            st.download_button("Download filtered CSV", csv, "filtered_output.csv")

        st.subheader("Advanced SQL Query (via DuckDB)")
        query = st.text_area("Enter SQL (e.g., SELECT * FROM df WHERE col1 = 'BUS0(SoundWire)'):",
                             "SELECT * FROM df LIMIT 10")
        if st.button("Run Query"):
            try:
                con = duckdb.connect()
                con.register("df", df)
                result = con.execute(query).fetchdf()
                st.dataframe(result)
            except Exception as e:
                st.error(f"Query failed: {e}")

        if os.name == 'nt':
            st.success("Returning control to PowerShell...")
            os.system("start powershell")
