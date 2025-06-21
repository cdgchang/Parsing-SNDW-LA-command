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
        # 檢查是否已有解析過的結果，若無則執行 parsing
        if 'raw_blocks' not in st.session_state or st.session_state.get("last_parsed_file") != str(filepath):
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
                                joined_block_words = '\n'.join(buffer).split()
                                if not any(word.lower() == exclude_keyword.lower() for word in joined_block_words):
                                    raw_blocks.append(buffer[:])
                                    match_count += 1
                            buffer = [line.strip()]  # start new block with timestamp line only
                        else:
                            if buffer and buffer[0].startswith("TimeStamp"):
                                buffer.append(line.strip())

                    if buffer:
                        joined_block_words = '\n'.join(buffer).split()
                        if not any(word.lower() == exclude_keyword.lower() for word in joined_block_words):
                            raw_blocks.append(buffer[:])
                            match_count += 1

                progress_bar.empty()
                status_text.text(f"Parsing complete. Matches found: {match_count}")

            st.session_state.raw_blocks = raw_blocks
            st.session_state.last_parsed_file = str(filepath)
        else:
            raw_blocks = st.session_state.raw_blocks

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

        # 根據 raw_blocks 做 2-row 組合：6 行的 block 做合併，其餘保留原樣
        two_line_data = []
        count_6_line = 0
        for block in raw_blocks:
            parsed_block = [re.split(r' {2,}|\t+', line.strip()) for line in block]
            if len(parsed_block) == 6:
                combined1 = parsed_block[0] + parsed_block[3]
                combined2 = parsed_block[1] + parsed_block[4]
                two_line_data.append(combined1)
                two_line_data.append(combined2)
                count_6_line += 1
            else:
                two_line_data.extend(parsed_block)  # 其餘 block 保留原樣

        if two_line_data:
            max_two_cols = max(len(row) for row in two_line_data)
            two_line_df = pd.DataFrame(two_line_data, columns=[f"col{i}" for i in range(max_two_cols)])
            two_line_df = two_line_df.loc[(two_line_df != '').any(axis=1)]
            two_line_df.index = [str(i+1) for i in range(len(two_line_df))]

            st.subheader("Parsed Data Table (2-row Format Mixed: merged + raw blocks)")
            st.dataframe(two_line_df)

            csv_two = two_line_df.to_csv(index=False)
            st.download_button("Download parsed CSV (2-row format)", csv_two, "parsed_output_2row.csv")

            # 額外統計資訊顯示
            total_blocks = len(raw_blocks)
            st.markdown(f"""
            ### Block Statistics
            - 🧩 Total blocks: **{total_blocks}**
            - ✅ 6-line blocks merged: **{count_6_line}** ({(count_6_line/total_blocks)*100:.1f}%)
            - 📄 Other blocks (raw): **{total_blocks - count_6_line}** ({((total_blocks - count_6_line)/total_blocks)*100:.1f}%)
            """)
        else:
            st.info("No data found for 2-row or raw block parsing.")
