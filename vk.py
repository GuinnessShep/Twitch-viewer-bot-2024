import os
import sys
import html
import requests
import urllib
from urllib.parse import parse_qs

import vk_api
from dotenv import load_dotenv
from win10toast import ToastNotifier

from cookie import createCookieFile


toast = ToastNotifier()
load_dotenv()
email = os.getenv('EMAIL')
pw = os.getenv('PASS')
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'


def parseResponse(response):
	headers = response.headers
	if headers['Content-Type'].find('application/json') != -1:
		return response.json()


def getVideo(cookie, output_dir, post_id, owner_id, video_id):
	
	url = 'https://vk.com/al_video.php'
	headers = {
		"Content-Type": "application/x-www-form-urlencoded",
		"X-Requested-With": "XMLHttpRequest",
		"User-Agent": user_agent,
		"Cookie": cookie
	}

	id = str(owner_id)+'_'+str(video_id)
	
	raw = {'act': 'show', 'al': 1, 'al_d': 0, 'autoplay': 0, 'list': '', 'module': '', 'video': id}	
	data = urllib.parse.urlencode(raw)
	print('Getting:', id, sep=" ")

	response = requests.post(url=url, data=data, headers=headers)
	json = parseResponse(response)
	payload_code = json['payload'][0]
	if payload_code == "8":
		print(f'video: {id} has been restricted')
		return
	hls = json['payload'][1][4]['player']['params'][0]['hls']
	#file_name = json['payload'][1][4]['player']['params'][0]['md_title']
	#file_name = html.unescape(file_name).replace("?","")

	hls_header = {
		"X-Requested-With": "XMLHttpRequest",
		"User-Agent": user_agent,
		"Cookie": cookie
	}
	#print(hls)
	response = requests.get(url=hls, headers=hls_header)
	hls_raw = response.text.splitlines()
	ts_raw = ''
	ts_sd = ''
	ts_low = ''
	ts_lowest = ''
	ts_mb = ''
	for i in range(len( hls_raw )):
		if hls_raw[i].find('QUALITY=sd') != -1:
			ts_sd = hls_raw[i+1]			
		elif hls_raw[i].find('QUALITY=low') != -1:
			ts_low = hls_raw[i+1]			
		elif hls_raw[i].find('QUALITY=lowest') != -1:
			ts_lowest = hls_raw[i+1]			
		elif hls_raw[i].find('QUALITY=mobile') != -1:
			ts_mb = hls_raw[i+1]

	if ts_sd != '':
		ts_raw = ts_sd
	elif ts_low != '':
		ts_raw = ts_low
	elif ts_lowest != '':
		ts_raw = ts_lowest
	elif ts_mb != '':
		ts_raw = ts_mb	
	
	response = requests.get(url=ts_raw, headers=hls_header)
	ts_m3u8 = response.text.splitlines()
	ts_list = []
	for i in range(len( ts_m3u8 )):
		if ts_m3u8[i].find('.ts') != -1:
			ts_list.append(ts_m3u8[i])

	print(f'total .ts: {len(ts_list)}')
	for ts in ts_list:
		print('download ts:', ts, sep=" ")
		#file_path = output_dir + '/' + ts
		file_path = output_dir + '/' + str(video_id) + '.ts'
		ts_url = ts_raw + ts
		
		response = requests.get(url=ts_url, headers=hls_header)
		with open(file_path, "ab") as file:				
			# write to file
			file.write(response.content)
	

def getPhoto(cookie, output_dir, photo, photo_id):
	header = {
		"X-Requested-With": "XMLHttpRequest",
		"User-Agent": user_agent,
		"Cookie": cookie
	}

	response = requests.get(url=photo['url'], headers=header)
	file_path = output_dir+"/"+str(photo_id)+".jpg"
	with open(file_path, "wb") as file: file.write(response.content)


def initApi(email, pw):
	vk_session = vk_api.VkApi(email, pw)	
	vk_session.auth()
	vk = vk_session.get_api()
	return vk

# owner_id=532641550, offset=0, count=20
def getWall(vk, cookie, owner_id, domain, offset=0, count=20, extended=1):
	if domain != '':
		res = vk.wall.get(domain=domain, offset=offset, count=count, extended=extended)
	elif owner_id != '':
		res = vk.wall.get(owner_id=owner_id, offset=offset, count=count, extended=extended)

	if ('items' in res) and ( len(res['items']) == 0 ):
		print(f'No Post Found')
		return

	# wall folder
	if ( 'profiles' in res ) and ( len(res['profiles']) != 0 ):
		wall_name = res['profiles'][0]['screen_name']
	elif ( 'groups' in res ) and ( len(res['groups']) != 0 ):
		wall_name = res['groups'][0]['screen_name']

	# create folder if not exist
	wall_name = html.unescape(wall_name)
	root_path = f'./{wall_name}'
	if not os.path.exists(root_path):
		os.makedirs(root_path)

	# number of posts
	print(f'Number of posts: {res["count"]}')
	
	items = res['items']
	for post in items:	
		post_id = post['id']
		output_dir = f'{root_path}/{str(post_id)}'
		if os.path.exists(output_dir):
			print('skip:', post_id, sep=" ")
			continue
		else: os.makedirs(output_dir)

		print('Getting Post:', post_id, sep=" ")
		if 'copy_history' in post:
			cp_hist = post['copy_history'][0]
			if 'attachments' in cp_hist:
				attachments = cp_hist['attachments']
			else: continue
		else:
			if 'attachments' in post:
				attachments = post['attachments']
			else: continue

		# attachments type: photo, video, link
		print(f'Number of attachments: {len(attachments)}')

		for attachment in attachments:
			if attachment['type'] == "video":
				owner_id = attachment['video']['owner_id']
				video_id = attachment['video']['id']
				duration = attachment['video']['duration']
				if duration != 0:
					getVideo(cookie, output_dir, post_id, owner_id, video_id)
			elif attachment['type'] == "photo":
				photo = attachment['photo']['sizes'][-1]
				photo_id = attachment['photo']['id']
				getPhoto(cookie, output_dir, photo, photo_id)							

		

if __name__ == "__main__":

	args = sys.argv[1:]
	# check number of args
	if len(args) < 3 or len(args) > 3:
		print('Wrong Arguments')
		print('Ex: python vk.py <domain> <offset> <count>')
		exit()

	# check offset and count is numeric
	if not args[1].isnumeric():
		print('Argument 2 (offset) must be numeric')
		exit()
	if not args[2].isnumeric():
		print('Argument 3 (count) must be numeric')
		exit()

	domain = str(args[0])
	offset = int(args[1])
	count = int(args[2])
	
	if offset < 0:
		print('Argument 2 (offset) must be >= 0')
		exit()
	if count < 1 or count > 100:
		print('Argument 3 (count) not in range (1-100)')
		exit()

	#if not os.path.exists('cookie.txt'):
	print('Getting Cookie')
	createCookieFile(email, pw)

	with open( 'cookie.txt', 'r' ) as f:
		cookie = f.read()

	print('Init Api')
	vk = initApi(email, pw)

	# count = 100 (max)
	owner_id = ''
	if domain.find('public') != -1 or domain.find('club') != -1:
		owner_id = domain.replace('public', '-').replace('club', '-')
		domain = ''
	
	getWall(vk, cookie, owner_id=owner_id, domain=domain, offset=offset, count=count)

	toast.show_toast("Vk Downloader","Download completed!",duration=3)
