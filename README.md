# KOHA_to_Unicat
Get library records from KOHA, transform and post to Unicat https://www.unicat.be/

## Installation
- copy both files to a folder on your hard drive
- set credential details in config_original.py and save as config.py
- if you run the script on a regular basis (e.g. weekly CRON job), set the frequency in the config.py accordingly (e.g. 7 [days])

## Usage
1. Launch the script (e.g. `$ python3 KOHA_to_Unicat.py`)
2. Enter the start date. There are 3 options:
    1. do not enter a value (or wait 60 seconds) → the records created or modified last week are processed
    2. type a date in the format YYYYMMDD (e.g. 20230501 for May 1, 2023) → all records created or modified after this date will be processed.
    3. type '0'→ all records will be processed (e.g. for an annual full dump)
3. Hit Enter

Result:
- selected records have been transformed to Unicat format
- the transformed records are written to the Unicat FTP server
- the transformed records are written to a local file
- the result is reported in a log file (log.txt)
