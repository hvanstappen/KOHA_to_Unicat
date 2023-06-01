# KOHA_to_Unicat
post library records from KOHA to Unicat

## Installation
- copy both files to a folder on your hard drive
- set credential details in config.py
- if you run the script on a regular basis (e.g. weekly CRON job), set the frequency in the config.py accordingly (e.g. 7 [days])

## Usage
- Launch the script (e.g. $ python3 KOGA_to_Unicat.py
- Enter the start date followed by Enter. There are 3 options:
-- do not enter a value and press Enter (or wait 60 seconds) → the records created or modified last week are processed
-- type a date in the format YYYYMMDD (e.g. 20230501 for May 1, 2023) → all records created or modified after this date will be processed.
-- type '0'→ all records will be processed (e.g. for an annual full dump)

Result:
- selected records have been transformed to Unicat format
-the transformed records are written to the Unicat FTP server
- the transformed records are written to a local file
- the result is reported in a log file (log.txt)
