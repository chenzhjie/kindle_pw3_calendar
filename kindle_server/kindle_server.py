from datetime import datetime
from zhdate import ZhDate
import urllib.request
from bs4 import BeautifulSoup
import os
import codecs
import requests
import json
import paramiko
import sqlite3

class forcast_weather:
    def __init__(self):
        self.date = ''
        self.text = ''
        self.temp_max = ''
        self.temp_min = ''

date_now = 0
text = ""
temp = ""
humidity = ""
temp_max = ""
temp_min = ""
forcast_day_1 = forcast_weather()
forcast_day_2 = forcast_weather()
forcast_day_3 = forcast_weather()

############
# Funktionen
def _exec(cmd):
	rc = os.system(cmd)
	if (rc != 0):
		print("`%s` failed with error %d" % (cmd, rc))
		exit(rc)

def get_date_now():
    global date_now
    date_now = datetime.now()

# return datetime like "2021-02-06"
def get_date():
    return date_now.strftime("%Y-%m-%d")

# return datetime like "10:24:28"
def get_time():
    return date_now.strftime("%H:%M:%S")

# return what day is today like "06"
def get_day():
    date_str = get_date()
    return date_str.split("-")[2]

def get_month():
    date_str = get_date()
    return date_str.split("-")[1]

# return the weekday is today like "周六"
def get_weekday():
    int2week = {0 : "周一", 1 : "周二", 2 : "周三", 
                3 : "周四", 4 : "周五", 5 : "周六", 6 : "周日"}
    week_day = date_now.weekday()
    return int2week[week_day]

# return lunar date like "农历2020年12月25日"
def get_lunar_date():
    return str(ZhDate.from_datetime(date_now))

# return what holladay today, else return " "
def get_holladay():
    today = get_day()
    root_url = 'https://wannianrili.51240.com/'
    response = urllib.request.urlopen(root_url)
    html = response.read()
    soup = BeautifulSoup(html, 'lxml')
    tag_soup = soup.find(class_='wnrl_k')
    if tag_soup == None:
        return " "
    else:
        detail = tag_soup.find_all(class_='wnrl_riqi')
        for i in range(len(detail)):
            result = detail[i].find(class_='wnrl_td_gl')
            if result:
                if result.get_text() == today:
                    result = detail[i].find(class_='wnrl_td_bzl wnrl_td_bzl_hong')
                    if result:
                        return result.get_text()
                    else:
                        return " "

def get_weather_data():
    CITY = "101280902" #广宁
    KEY = "8059baef6cb1476090df16f71668f3cc"

    WEATHER_FORCAST_API_URL = "https://devapi.heweather.net/v7/weather/3d"
    WEATHER_NOW_API_URL = "https://devapi.qweather.com/v7/weather/now"
    weather_forcast_url = WEATHER_FORCAST_API_URL + '?location=' + CITY + '&key=' + KEY
    weather_now_url = WEATHER_NOW_API_URL + '?location=' + CITY + '&key=' + KEY

    weather_forcast_res = requests.get(weather_forcast_url)
    weather_forcast_res = json.loads(weather_forcast_res.text)
    with open('weather_forcast_res.json', 'w') as f:
        json.dump(weather_forcast_res, f)

    weather_now_res = requests.get(weather_now_url)
    weather_now_res = json.loads(weather_now_res.text)
    with open('weather_now_res.json', 'w') as f:
        json.dump(weather_now_res, f)

def parse_weather_data():
    global text, temp, humidity, temp_max, temp_min, forcast_day_1, forcast_day_2, forcast_day_3
    with open('weather_forcast_res.json', 'r') as f:
        weather_forcast_res = json.load(f)

    with open('weather_now_res.json', 'r') as f:
        weather_now_res = json.load(f)

    text = str(weather_now_res['now']['text'])
    temp = weather_now_res['now']['temp']
    humidity = weather_now_res['now']['humidity']

    temp_max = weather_forcast_res['daily'][0]['tempMax']
    temp_min = weather_forcast_res['daily'][0]['tempMin']

    fxdate_result = (str(weather_forcast_res['daily'][0]['fxDate'])).split("-")
    forcast_day_1.date = fxdate_result[1] + "-" + fxdate_result[2]
    forcast_day_1.text = text
    forcast_day_1.temp_max = weather_forcast_res['daily'][0]['tempMax']
    forcast_day_1.temp_min = weather_forcast_res['daily'][0]['tempMin']

    fxdate_result = (str(weather_forcast_res['daily'][1]['fxDate'])).split("-")
    forcast_day_2.date = fxdate_result[1] + "-" + fxdate_result[2]
    forcast_day_2.text = weather_forcast_res['daily'][1]['textDay']
    forcast_day_2.temp_max = weather_forcast_res['daily'][1]['tempMax']
    forcast_day_2.temp_min = weather_forcast_res['daily'][1]['tempMin']

    fxdate_result = (str(weather_forcast_res['daily'][2]['fxDate'])).split("-")
    forcast_day_3.date = fxdate_result[1] + "-" + fxdate_result[2]
    forcast_day_3.text = weather_forcast_res['daily'][2]['textDay']
    forcast_day_3.temp_max = weather_forcast_res['daily'][2]['tempMax']
    forcast_day_3.temp_min = weather_forcast_res['daily'][2]['tempMin']
    

# svg convert
def svg_convert():
    PATH = os.getcwd()
    SVG_OUTPUT = "%s/cron_kindle-wetter_output.svg" % PATH
    SVG_FILE = "%s/cron_kindle-wetter_preprocess.svg" % PATH
    TMP_OUTPUT = "%s/cron_kindle-wetter_tmp.png" % PATH
    OUTPUT = "%s/cron_kindle-wetter.png" % PATH
    UPLOAD = "/root/images/cron_kindle-wetter.png"
    SQLPATH = "/home/cubie/.homeassistant/home-assistant_v2.db"

    conn = sqlite3.connect(SQLPATH)
    cursor = conn.cursor()
    sql_text_temp = "SELECT state FROM states WHERE entity_id='sensor.living_room_temperature' ORDER BY state_id DESC LIMIT 1"
    sql_text_hum = "SELECT state FROM states WHERE entity_id='sensor.living_room_humidity' ORDER BY state_id DESC LIMIT 1"
    cursor.execute(sql_text_temp)
    temp_room_str = str(cursor.fetchone()[0])
    # print(temp_room_str)
    cursor.execute(sql_text_hum)
    hum_room_str = str(cursor.fetchone()[0])
    # print(hum_room_str)
    

    datetime_str = get_date()
    weekday_str = get_weekday()
    day_str = get_day()
    lunar_str = get_lunar_date()
    holladay_str = get_holladay()
    time_str = get_time()

    output = codecs.open(SVG_FILE, "r", encoding="utf-8").read()
    output = output.replace("$DATE", datetime_str)
    output = output.replace("$TIME", time_str)
    output = output.replace("$WEEK", weekday_str)
    output = output.replace("$D", day_str)
    output = output.replace("$LUNAR", lunar_str)
    output = output.replace("$HD", holladay_str)

    output = output.replace("$TEXT", text)
    output = output.replace("$CT", temp)
    output = output.replace("$CHH", temp_max)
    output = output.replace("$CHL", temp_min)
    output = output.replace("$CL", humidity)

    output = output.replace("$CHR", temp_room_str)
    output = output.replace("$CR", hum_room_str)

    output = output.replace("$FD1", forcast_day_1.date)
    output = output.replace("$T1", forcast_day_1.text)
    output = output.replace("$TX1", forcast_day_1.temp_max)
    output = output.replace("$TN1", forcast_day_1.temp_min)

    output = output.replace("$FD2", forcast_day_2.date)
    output = output.replace("$T2", forcast_day_2.text)
    output = output.replace("$TX2", forcast_day_2.temp_max)
    output = output.replace("$TN2", forcast_day_2.temp_min)

    output = output.replace("$FD3", forcast_day_3.date)
    output = output.replace("$T3", forcast_day_3.text)
    output = output.replace("$TX3", forcast_day_3.temp_max)
    output = output.replace("$TN3", forcast_day_3.temp_min)

    codecs.open(SVG_OUTPUT, "w", encoding="utf-8").write(output)
    #_exec("rsvg-convert --background-color=white -o %s %s" % (TMP_OUTPUT, SVG_OUTPUT))
    _exec("inkscape --without-gui --export-width 1072 --export-height 1448 --export-background=WHITE --export-png %s %s 1>/dev/null 2>&1" % (TMP_OUTPUT, SVG_OUTPUT))
    _exec("convert %s -type GrayScale -depth 8 -colors 256 %s 1>/dev/null 2>&1" % (TMP_OUTPUT, OUTPUT))

    private_key = paramiko.RSAKey.from_private_key_file("/home/cubie/.ssh/guizhou/guizhou")
    transport = paramiko.Transport(('116.63.187.227', 22))
    transport.connect(username="root", pkey=private_key)
    sftp = paramiko.SFTPClient.from_transport(transport)
    #将Backdoor.exe 上传到192.168.0.104 '/tmp/Backdoor.exe'
    sftp.put(OUTPUT,UPLOAD)

    #	_exec("pngcrush -c 0 -ow %s 1>/dev/null 2>&1" % TMP_OUTPUT)
    #	_exec("mv -f '%s' '%s'" % (TMP_OUTPUT, OUTPUT))
    #	_exec("rm -f '%s'" % SVG_OUTPUT)

if __name__ == "__main__":
    get_date_now()
    get_weather_data()
    parse_weather_data()
    svg_convert()