from pyperi import Peri
import sys, time, os, getopt, csv
import os.path
import subprocess

broadcastdict = {}
deleteuser = []
pp = Peri()
p = {}
p1 = {}
HLS_URL_1 = "https://periscope-prod-eu-central-1.global.ssl.fastly.net/vidmanlive/"
HLS_URL_3 = "/playlist.m3u8"
livebroadcast = 0

def file_size(fname):
        import os
        statinfo = os.stat(fname)
        return statinfo.st_size


while True:
	#read users.csv into list every loop, so you can edit csv file during run.
	with open("users.csv", 'r') as readfile:
		reader = csv.reader(readfile, delimiter=',')
		usernames2 = list(reader)
	usernames = usernames2[0]
	
	deleteuserbroadcast = []
	for user in usernames:
		print ("Poll ", user)
		broadcast_history = pp.get_user_broadcast_history(username=user)
		if broadcast_history == ['unknown']:
			# user does not exists anymore
			# extra loop
			if user in deleteuser:
				if user in broadcastdict:
					del broadcastdict[user]
				usernames.remove(user)
				deleteuser.remove(user)
				print ("Delete user: ", user)
				with open("users.csv", 'w') as outfile:
					writer = csv.writer(outfile, delimiter=',',quoting=csv.QUOTE_ALL)
					writer.writerow(usernames)
			else:
				deleteuser.append(user)
				print ("Loop delete user")
			break
		if not broadcast_history:
			# no broadcast history
			if user in broadcastdict:
				broadcastdict[user]['state'] = 'ENDED'
		for key in broadcast_history:
			# check for RUNNING scope.
			if key['state']== 'RUNNING':
				livebroadcast = 1
				if user not in broadcastdict:
					print ("New scope of user: ", user)
					broadcast_id = key['id']
					HLS_URL_2 = key['image_url'][24:]
					if "chunk" in HLS_URL_2:
						chunkpos = HLS_URL_2.find('chunk') - 1
						HLS_URL_2 = HLS_URL_2[:chunkpos]
					#when no chunk in string
					if "orig.jpg" in HLS_URL_2:
						chunkpos = HLS_URL_2.find('orig.jpg') - 1
						HLS_URL_2 = HLS_URL_2[:chunkpos]
					broadcastdict[user] = {}
					broadcastdict[user]['broadcast_id'] = broadcast_id
					broadcastdict[user]['HLS_URL']= HLS_URL_1 + HLS_URL_2 + HLS_URL_3
					broadcastdict[user]['state']= 'RUNNING'
					broadcastdict[user]['time']= time.time()
					fileusername = user.lower()
					broadcastdict[user]['filename']= fileusername + '_on_peri_' + str(broadcastdict[user]['time'])[:10] + '.mkv'
					broadcastdict[user]['filesize']= 0
					broadcastdict[user]['recording']= 0
		if livebroadcast == 0:
			#no live broadcasts for this user found
			if user in broadcastdict:
				broadcastdict[user]['state'] = 'ENDED'
				print (user, ': ', key['id'])
				print ("broadcast ended")
				deleteuserbroadcast.append(user)
		livebroadcast = 0
	#check if file still growing
	for user in broadcastdict:
		if broadcastdict[user]['recording'] == 1 and os.path.exists(broadcastdict[user]['filename']):
			if broadcastdict[user]['filesize'] < file_size(broadcastdict[user]['filename']):
				broadcastdict[user]['filesize'] = file_size(broadcastdict[user]['filename'])
				print ("Running recording: ", broadcastdict[user]['filename'])
			else:
				print ("End recording for: ", broadcastdict[user]['filename'] , " :stream error")
				p[user].terminate()
				deleteuserbroadcast.append(user)
	#start stop recordings
	for user in broadcastdict:
		if broadcastdict[user]['recording'] == 0 and broadcastdict[user]['state'] == 'RUNNING':
			# start recording
			print ("Start recording for: ", user)
			input = broadcastdict[user]['HLS_URL']
			output = broadcastdict[user]['filename']
			command = ['ffmpeg.exe','-i' , input,'-y','-acodec','mp3','-loglevel','0', output]
			p[user]=subprocess.Popen(command)
			broadcastdict[user]['recording'] = 1
			time.sleep(3)
		if broadcastdict[user]['state'] == 'ENDED' and broadcastdict[user]['recording'] == 1:
			# end recording and delete in broadcastdict
			print ("End recording for: ", user)
			p[user].terminate()
			deleteuserbroadcast.append(user)
	#check if new recording file is created
	for user in broadcastdict:
		if not os.path.exists(broadcastdict[user]['filename']):
			time.sleep(10)
			if not os.path.exists(broadcastdict[user]['filename']):
				print ("No recording file created for: ", user, "file: ", broadcastdict[user]['filename'])
				p[user].terminate()
				deleteuserbroadcast.append(user)
	#delete entry in broadcastdict and convert mkv -> mp4
	for user in deleteuserbroadcast:
		if user in broadcastdict:
			input = broadcastdict[user]['filename']
			output = input.replace('.mkv','.mp4')
			command = ['ffmpeg.exe','-i' , input,'-y','-loglevel','0', output]
			p1[user]=subprocess.Popen(command)
			del broadcastdict[user]
	time.sleep(1)
