RECORD_PERI

Record_peri.py is a simple Python scipt for recording Periscope live broadcasts of users stored in a csv.
Requirements:
- Python 3
	https://www.python.org/
- ffmpeg
	https://ffmpeg.org/

For users in the csv you need the Periscope account name.
e.g. @abc123 is user abc123.
A Twitter account name doesn't work.

Because ffmpeg can't stop decent with a script, the mkv isn't closed correctly.
At the end the mkv is converted to a good working mp4 file.
