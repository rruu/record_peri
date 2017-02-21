# Record_peri.py is a simple Python script for recording live Periscope scopes of users stored in a csv file.
# Put record_peri.py and the cvs file in the same directory. Recordings will also be stored in that directory.
# Advice: max 10 users in csv.
# You can run record-peri.py multiple times, when you create multiple directories, each with his own
# record_peri.py and csv file.
# It is possible te edit the csv file while record_peri.py is running.
# Use Notepad++ for editing.
#
# Requirements:	- Python 3
#				- ffmpeg

from bs4 import BeautifulSoup
import sys, time, os, getopt, csv
import os.path
import subprocess
import json
import urllib.request, urllib.error

PERISCOPE_URL = 'https://www.periscope.tv/'
HLSURL1 = [
	'https://periscope-prod-eu-central-1.global.ssl.fastly.net/vidmanlive/',
	'https://periscope-prod-sa-east-1.global.ssl.fastly.net/vidmanlive/',
	'https://periscope-prod-ap-northeast-1.global.ssl.fastly.net/vidmanlive/',
	'https://periscope-prod-us-east-1.global.ssl.fastly.net/vidmanlive/',
	'https://periscope-prod-ap-southeast-1.global.ssl.fastly.net/vidmanlive/',
	'https://periscope-prod-eu-west-1.global.ssl.fastly.net/vidmanlive/'
	]
HLS_URL_3 = "/playlist.m3u8"
broadcastdict = {}
deleteuser = []
p = {}
p1 = {}

def file_size(fname):
        import os
        statinfo = os.stat(fname)
        return statinfo.st_size

def get_live_broadcast(user):
	req = urllib.request.Request(PERISCOPE_URL + user)
	try:
		response = urllib.request.urlopen(req)
		r = response.read()
		soup = BeautifulSoup(r, 'html.parser')
		page_container = soup.find(id='page-container')
		data_store = json.loads(page_container['data-store'])
		broadcasts = data_store['BroadcastCache']['broadcasts']
		if not broadcasts:
			live_broadcast = {}
		else:
			for key in broadcasts:
				broadcast = broadcasts[key]
				if broadcast['broadcast']['state']== 'RUNNING':
					live_broadcast = broadcast['broadcast']['data']
					break
				else:
					live_broadcast = {}	
	except urllib.error.URLError as e:
		print("URLError: ",e.reason)
		res = e.reason
		if res == "Not Found":
			live_broadcast = {'user_id': ['unknown']}
		else:
			#unknown error
			live_broadcast = {'user_id': ['skip']}
	return live_broadcast
	
def rec_ffmpeg(user, input, output):
	command = ['ffmpeg.exe','-i' , input,'-y','-acodec','mp3','-loglevel','0', output]
	p[user]=subprocess.Popen(command)
	broadcastdict[user]['recording'] = 1
	time.sleep(1)

while True:
	#read users.csv into list every loop, so you can edit csv file during run.
	with open("users.csv", 'r') as readfile:
		reader = csv.reader(readfile, delimiter=',')
		usernames2 = list(reader)
	usernames = usernames2[0]
	
	deleteuserbroadcast = []
	for user in usernames:
		print ("Poll ", user)
		live_broadcast = get_live_broadcast(user)
		if not live_broadcast:
			if user in broadcastdict:
				print (user, ': broadcast ended')
				deleteuserbroadcast.append(user)
				broadcastdict[user]['state'] = 'ENDED'
		elif live_broadcast['user_id'] == ['unknown']:
			# user does not exists anymore
			# extra loop
			if user in deleteuser:
				if user in broadcastdict:
					deleteuserbroadcast.append(user)
				usernames.remove(user)
				deleteuser.remove(user)
				print ("Delete user: ", user)
				with open("users.csv", 'w') as outfile:
					writer = csv.writer(outfile, delimiter=',',quoting=csv.QUOTE_ALL)
					writer.writerow(usernames)
			else:
				deleteuser.append(user)
				print ("Loop delete user: ", user)
			break
		elif live_broadcast['user_id'] == ['skip']:
			#skip user loop
			print ("HTTP request error. Skip user: ", user)
		else:
			if user not in broadcastdict:
				print ("New scope of user: ", user)
				broadcast_id = live_broadcast['id']
				HLS_URL_2 = live_broadcast['image_url'][24:]
				if "chunk" in HLS_URL_2:
					chunkpos = HLS_URL_2.find('chunk') - 1
					HLS_URL_2 = HLS_URL_2[:chunkpos]
				if "orig.jpg" in HLS_URL_2:
					chunkpos = HLS_URL_2.find('orig.jpg') - 1
					HLS_URL_2 = HLS_URL_2[:chunkpos]
				broadcastdict[user] = {}
				broadcastdict[user]['broadcast_id'] = broadcast_id
				broadcastdict[user]['HLS_URL']= HLS_URL_2 + HLS_URL_3
				broadcastdict[user]['state']= 'RUNNING'
				broadcastdict[user]['time']= time.time()
				broadcastdict[user]['filename']= user + '_on_peri_' + str(broadcastdict[user]['time'])[:10] + '.mkv'
				broadcastdict[user]['filesize']= 0
				broadcastdict[user]['recording']= 0
				broadcastdict[user]['streamerror'] = 0
	#check if file still growing
	for user in broadcastdict:
		if broadcastdict[user]['recording'] == 1 and os.path.exists(broadcastdict[user]['filename']):
			if broadcastdict[user]['filesize'] < file_size(broadcastdict[user]['filename']):
				broadcastdict[user]['filesize'] = file_size(broadcastdict[user]['filename'])
				broadcastdict[user]['streamerror'] = 0
				print ("Running recording: ", broadcastdict[user]['filename'])
			else:
				if broadcastdict[user]['streamerror'] == 1:
					#extra loop
					print ("End recording for: ", broadcastdict[user]['filename'] , " :stream error")
					deleteuserbroadcast.append(user)
				else:
					broadcastdict[user]['streamerror'] = 1
	#start stop recordings
	for user in broadcastdict:
		if broadcastdict[user]['recording'] == 0 and broadcastdict[user]['state'] == 'RUNNING':
			print ("Start recording for: ", user)
			for key in HLSURL1:
				URL = key + broadcastdict[user]['HLS_URL']
				rec_ffmpeg(user, URL, broadcastdict[user]['filename'] )
				if os.path.exists(broadcastdict[user]['filename']):
					print ('Recording started from: ', key)
					break
				else:
					p[user].terminate()
			if not os.path.exists(broadcastdict[user]['filename']):
				print ("No recording file created for: ", user, "file: ", broadcastdict[user]['filename'])
				deleteuserbroadcast.append(user)
		if broadcastdict[user]['state'] == 'ENDED' and broadcastdict[user]['recording'] == 1:
			# end recording
			print ("End recording for: ", user)
			deleteuserbroadcast.append(user)
	#end recording, delete entry in broadcastdict and convert mkv -> mp4
	for user in deleteuserbroadcast:
		p[user].terminate()
		if user in broadcastdict:
			input = broadcastdict[user]['filename']
			output = input.replace('.mkv','.mp4')
			command = ['ffmpeg.exe','-i' , input,'-y','-loglevel','0', output]
			#p1[user]=subprocess.Popen(command)
			del broadcastdict[user]
	time.sleep(1)
