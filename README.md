🧾 Hex Log Parser (Streamlit App)
This is an interactive web-based application built with Streamlit. It parses and visualizes .txt Hex log files with block separation, keyword filtering, data table output, and CSV export capabilities.

📂 Features
✅ Input & Filtering
Accepts full path to a .txt log file

Supports exclusion of blocks containing specified keywords (e.g., Ping, Debug)

Automatically identifies new blocks based on lines containing TimeStamp

📊 Data Visualization
Original 4-line Raw Data

Displays parsed data block-by-block

Downloadable as parsed_output_4row.csv

2-row Format View

Automatically merges blocks of exactly 6 lines into 2 rows (combined format)

Other blocks are preserved in raw format

Downloadable as parsed_output_2row.csv

Block Statistics

Total number of parsed blocks

Number and percentage of 6-line merged blocks

Remaining raw blocks count and ratio

🧰 Technical Overview
Built using Streamlit for interactive UI

Uses pandas for data manipulation and re for block parsing

Utilizes session_state to avoid re-parsing the same file

duckdb is imported for potential SQL-style queries (not active in current version)

🚀 How to Run
1. Install dependencies
bash
複製
編輯
pip install streamlit pandas duckdb
2. Launch the App
bash
複製
編輯
streamlit run streamlit_hexparser.py
📥 Output Files
parsed_output_4row.csv: Raw block-parsed data table

parsed_output_2row.csv: Processed 2-row format table with merged 6-line blocks

📌 Notes
The log file must contain "TimeStamp" markers to separate blocks

Keyword filtering is case-insensitive and excludes any block containing the keyword

For large files, progress is shown while parsing (by bytes read)

📷 UI Preview (Optional)
You can add screenshots here showing:

File input

Table views (4-line / 2-row)

Download buttons

Block statistics summary

Would you like a markdown file version (README.md) ready to copy/paste, or exported? I can generate it right away.
