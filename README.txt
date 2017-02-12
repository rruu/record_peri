RECORD_PERI

Record_peri.py is an example Python script how you can use PyPeri.
It can record Periscope live broadcasts of users stored in a csv.
Requirements:
- Python 3
	https://www.python.org/
- PyPeri
	https://pyperi.readthedocs.io/en/latest/
- ffmpeg
	https://ffmpeg.org/

Sometimes the script crashes on unexpected errors.
Use the run_record_peri.py to keep the script running.

For users in the csv you need the Periscope account name.
e.g. @abc123 is user abc123.
A Twitter account name doesn't work.

When an user doesn't exists anymore, PyPeri gives an error.
I made a small mod in the pyperi.py to return an "unknown".
Place this pyperi.py in the same directory as the record_peri.py.