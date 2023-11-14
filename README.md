# pyWebTextsScaper
Scap English vocabularies from websites

# HOW TO
python3 wvsc.py [OPTIONS] URL(s)

Example:
- Scap vocabularies from https://google.com, print verbose logs and save result to file  *vocabularies.sqlite3*:
  - python3 wvsc.py --verbose=true http://google.com --output=vocabularies.sqlite3
- Scap vocabularies from websites in url database file named *urls.sqlite3*, print verbose logs and save result to file *vocabularies.sqlite3*:
  - python3 wvsc.py --verbose=true --input=urls.sqlite3 --output=vocabularies.sqlite3

## URL(s)
  Specified URL(s) to scrap. Multiple URLs are accepted

## OPTIONS
### -h/--help
  - Print help

### -v/--verbose
  - Print many as many runtime logs

### -i/--input
  - Input URL(s) database file. Database formats are determined by file extensions(.sqlite3, .txt). Supported formats are sqlite3 and text. If specified file is in text format, the file must contains list of URLs seperated by new line. If specified file is in sqlite3 format, the file must contains a table named *urls* with at least one column named *url*

### -o/--output
  - Output file to store scraped vocabularies. File format is determined by file extension(.sqlite3, .json or .txt). If a text file is specified, vocabularies will be stored to file line by line. If a json file is specified, vocabularies will be stored as a json array. If a sqlite3 file is specified, a table named *vocabularies* with 3 columns (*id*,*name*,*occurrences*) will be created to store vocabularies. If vocabularies are already exist in output file, they will be updated but not overriden.