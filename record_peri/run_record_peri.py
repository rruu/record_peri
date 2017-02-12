import subprocess, time

command = ['python','record_peri.py']
p=subprocess.Popen(command)
while True:
	while p.poll() is None:
		time.sleep(1)
	print ("Process ended, ret code:", p.returncode)
	print ("Restart")
	p=subprocess.Popen(command)

