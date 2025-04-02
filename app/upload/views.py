from __future__ import unicode_literals
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import cv2
import numpy
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
from io import BytesIO
from upload.validations.upload_validation import MyValidationForm
import PIL.ExifTags
from django.core.exceptions import ValidationError
import logging
import datetime
import os
from pillow_heif import register_heif_opener
import piexif
from pathlib import Path
import json
import re
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import youtube_dl
import yt_dlp

register_heif_opener()

logger = logging.getLogger("django")
# import os
# import time
def crawl(request):
    options = webdriver.ChromeOptions()
    # options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--user-data-dir=/usr/src/app/userdata/selenium")
    # options.add_argument("disable-dev-shm-usage")
    # options.add_argument("--no-sandbox")
    # options.add_argument("start-maximized")
    # # options.add_argument("--headless")
    # options.add_argument("disable-gpu")
    # options.add_argument("--disable-extensions")
    # options.headless = True
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--start-maximized")
    # options.binary_location = "/usr/bin/google-chrome"
    options.add_argument('--disable-gpu') # for headless
    # options.add_argument('--disable-dev-shm-usage') # uses /tmp for memory sharing
    # # disable popups on startup
    # options.add_argument('--no-first-run')
    # options.add_argument('--no-service-autorun')
    # options.add_argument('--no-default-browser-check')
    # options.add_argument('--password-store=basic')
    options.add_argument("--no-sandbox")
    # logger.info('options %s',options)
    driverPath = "/usr/bin/chromedriver"
    browser = webdriver.Chrome(driverPath, chrome_options=options)
    # browser = webdriver.Chrome()
    browser.get('https://stackoverflow.com/questions/tagged/php+laravel?sort=MostVotes&days=600&page=2&pagesize=50')

    soup = BeautifulSoup(browser.page_source, 'html.parser')

    # posts = soup.find_all('h3', class_='s-post-summary--content-title')
    posts = soup.find_all('div', class_=['s-post-summary','js-post-summary'])
    links = []
    for post in posts:
        hasAnswer = post.find('div', class_='s-post-summary--stats-item has-answers has-accepted-answer')
        # logger.info('hasAnswer %s', hasAnswer)
        if hasAnswer is None : continue
        answerPost = post.find('h3', class_='s-post-summary--content-title')
        if answerPost is None :continue
        iLinks = answerPost.findChildren("a", recursive=False)
        for iLink in iLinks:
            links.append(iLink)
    # links=soup.find_all('h3', class_='s-post-summary--content-title')
    # links=

    for link in links:
        # logger.info('link :%s',link['href'])
        # print('link :' + link['href'] )
        browser.get("https://stackoverflow.com" + link['href'])
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        # logger.info('soup %s', soup)
        content = getattr(soup.find('div',class_='js-post-body'),'text','')
        anwerCell = soup.select('div.answer.accepted-answer')
        # logger.info('anwerCell %s', anwerCell)
        if len(anwerCell) == 0:
            anwser = ''
        else:
            anwser = getattr(anwerCell[0].find('div',class_='js-post-body'),'text','')
        # logger.info('link :\n%s , content :\n %s, anwser : \n%s',link['href'],content.replace('\n',' ').strip(), anwser.replace('\n',' ').strip())
        logger.info('<<<<\nLINK : https://stackoverflow.com%s\n TITLE : %s\n CONTENT : %s\n ANWSER : %s \n>>>>\n',link['href'],link.text.strip(), content.strip(), anwser.strip())
        # print('link :' + link['href'] , 'cotent :' + soup.find('div',class_='post-text').text.replace('\n',' ').strip())
    browser.quit()
    return render(request,"crawl.html")

def image_convert(request):
    origin_media_path = str(settings.MEDIA_ROOT) + "/origin"
    convert_media_path = str(settings.MEDIA_ROOT) + "/convert"
    Path(origin_media_path).mkdir(parents=True, exist_ok=True)
    Path(convert_media_path).mkdir(parents=True, exist_ok=True)
    result = convert_heic_to_jpeg(origin_media_path,convert_media_path)
    return render(request,"convert.html")

def bulkWrite(rgbaList,textColor,outerBorderBgr):
    media_path = str(settings.MEDIA_ROOT) + "/convert"
    write_path = str(settings.MEDIA_ROOT) + "/done"
    Path(media_path).mkdir(parents=True, exist_ok=True)
    Path(write_path).mkdir(parents=True, exist_ok=True)
    for fileName in os.listdir(media_path):
        logger.info('fileName %s',fileName)
        filePath = media_path + "/" + fileName
        writePath = write_path + "/" + fileName
        writeImage(filePath,writePath,rgbaList,textColor,outerBorderBgr)
def writeImage(filePath,writePath,rgbaList,textColor,outerBorderBgr):
    writeText = getDatetimeFromFilePath(filePath)
    virat_img = cv2.imread(filePath)
    height, width, channels = virat_img.shape
    writeBorder(virat_img,10,int(height / 40),int(height / 160),int(height / 160),rgbaList,path=writePath)
    # secondBorder
    virat_img = cv2.imread(writePath)
    writeBorder(virat_img,2,2,2,2,outerBorderBgr,path=writePath)
    if writeText != "unknown":
         insert_text(writePath,writePath, height, writeText,textColor)
def image_upload(request):
    # print('__name__',__name__)
    
    fs = FileSystemStorage()
    media_path = settings.MEDIA_ROOT
    # logger.info('root path %s',os.listdir(media_path)[1])
    form = MyValidationForm()
    # bulkWrite()
    if (
        request.method == "POST"
        # and "image_file" in request.FILES
        # and request.FILES["image_file"]
    ):
        request.session["text_color_rgba"] = getRgba(request.POST.get("text_color_rgba", "rgba(0,0,0,1)"),"rgba(0,0,0,1)")
        request.session["rgba_color"] = getRgba(request.POST.get("rgba_color", "rgba(0,0,0,0)"),"rgba(0,0,0,0)")
        request.session["outer_rgba_color"] = getRgba(request.POST.get("outer_rgba_color", "rgba(0,0,0,0)"),"rgba(0,0,0,0)") 

        # logger.debug("outer_rgba_color %s", request.session.get("outer_rgba_color"))
        # logger.info(
        #     "rgba_color %s %s",
        #     request.session.get("rgba_color"),
        #     request.session,
        # )
        rgbaList = getBrgList(request.session.get("rgba_color"))
        textColor = getBrgList(request.session.get("text_color_rgba"))
        outerBorderBgr = getBrgList(request.session["outer_rgba_color"])
        bulkWrite(rgbaList=rgbaList,textColor=textColor,outerBorderBgr=outerBorderBgr)
        # logger.info('rgbaTuple %s',rgbaList)
        # image_file = request.FILES["image_file"]
        # Both the variables would contain time
        # elapsed since EPOCH in float
        # ti_c = os.path.getctime(path)
        # ti_m = os.path.getmtime(path)

        # # Converting the time in seconds to a timestamp
        # c_ti = time.ctime(ti_c)
        # m_ti = time.ctime(ti_m)
        # imgStream = image_file.read()
        # writeText = getDatetime(imgStream)
        # logger.info('writetext %s', writeText)
        # # reading the image
        # # virat_img = cv2.imread(img)

        # # making border around image using copyMakeBorder
        

        # # showing the image with border
        # path = str(media_path) + "/" + image_file.name
        # # first border
        # virat_img = cv2.imdecode(
        #     numpy.fromstring(imgStream, numpy.uint8), cv2.IMREAD_ANYCOLOR
        # )
        # height, width, channels = virat_img.shape
        # writeBorder(virat_img,10,int(height / 40),int(height / 160),int(height / 160),rgbaList,path=path)
        # # secondBorder
        # virat_img = cv2.imread(path)
        # writeBorder(virat_img,2,2,2,2,outerBorderBgr,path=path)
        # insert_text(path, height, writeText,textColor)
        # # text

        # # filename = fs.save(image_file.name, image_file)
        # # image_url = fs.url(filename)
        # print("post")
        # print(image_url)
        return redirect("upload")
    else:
        # for f in fs.listdir(media_path):
        #     print (fs.url(f))
        logger.info(
            "get request from session text_color_rgba: %s rgba_color: %s",
            request.session.get("text_color_rgba"),
            request.session.get("rgba_color"),
        )
        myfiles = []
        done_path = str(media_path) + "/" + "done"
        Path(done_path).mkdir(parents=True, exist_ok=True)
        for f in fs.listdir(done_path)[1]:
            myfiles.append(fs.url("done/" + f))
        # myfiles = [f for f in fs.listdir(media_path) if isfile(join(media_path, f))]
        # logger.info('urls %s',myfiles)
        # print("test", len(myfiles), "\n", myfiles)
        return render(
            request,
            "upload.html",
            {
                "image_urls": myfiles,
                "form": form,
                "text_color_rgba": getRgba(request.session.get("text_color_rgba") or "rgba(0,0,0,1)","rgba(0,0,0,1)"),
                "rgba_color": getRgba(request.session.get("rgba_color") or "rgba(0,0,0,0)","rgba(0,0,0,0)"),
                "outer_rgba_color": getRgba(request.session.get("outer_rgba_color") or "rgba(0,0,0,0)","rgba(0,0,0,0)"),
            },
        )


def insert_text(path: str,writePath:str, originHeight, text:str,textColor):
    img = cv2.imread(path)
    height, width, channels = img.shape
    # print(height, width, channels)

    # font
    font = cv2.FONT_HERSHEY_SCRIPT_COMPLEX | cv2.FONT_ITALIC

    # org
    orgBottom = height - int((height - originHeight) / 3)
    org = (50, orgBottom)

    # fontScale
    fontScale = (height / 1500)/2.2

    # Red color in BGR
    # color = (0, 0, 0)
    print(f"here")

    # Line thickness of 2 px
    thickness = int(height / 1500)

    # Using cv2.putText() method
    logger.info('text -> %s,fontScale-> %s,height -> %s, width-> %s',text,fontScale,height, width)
    img = cv2.putText(
        img, text, org, font, fontScale, textColor, thickness, cv2.LINE_AA, False
    )
    cv2.imwrite(writePath, img)


def get_exif(uploadedImageStream):
    pImage = Image.open(BytesIO(uploadedImageStream))
    exif = (
        {PIL.ExifTags.TAGS[k]: v for k, v in pImage._getexif().items() if k in TAGS}
        if pImage._getexif() is not None
        else {}
    )
    # logger.info("fullexif %s", exif)
    exifdata = pImage.getexif()
    for tag_id, data in exifdata.items():

        # Get the tag name, instead of the tag ID
        tag_name = TAGS.get(tag_id, tag_id)
        # logger.info("TAGS[tag_id] %s", TAGS[tag_id])
        # logger.info(f"{tag_name:25}: {data}")

    # logger.info("exifdata", exifdata)
    geo = get_geo(exifdata)
    print("geo", geo)
    for tagid in exifdata:
        # getting the tag name instead of tag id
        tagname = TAGS.get(tagid, tagid)
        print("tagName", tagname)

        # passing the tagid to get its respective value
        value = exifdata.get(tagid)
        print("value", value)


def get_geo(exif):
    for key, value in TAGS.items():
        if value == "GPSInfo":
            break
        gps_info = exif.get_ifd(key)
    return {GPSTAGS.get(key, key): value for key, value in gps_info.items()}

def getDatetime(uploadedImageStream):
    pImage = Image.open(BytesIO(uploadedImageStream))
    exifdata = pImage.getexif()
    for tag_id, data in exifdata.items():
        # Get the tag name, instead of the tag ID
        tag_name = TAGS.get(tag_id, tag_id)
        if tag_name == "DateTime":
            return datetime.datetime.strptime(data.split(" ")[0], '%Y:%m:%d').strftime('%A') + ", " + data
    return 'unknown'

def getDatetimeFromFilePath(filePath):
    pImage = Image.open(filePath)
    exifdata = pImage.getexif()
    for tag_id, data in exifdata.items():
        # Get the tag name, instead of the tag ID
        tag_name = TAGS.get(tag_id, tag_id)
        if tag_name == "DateTime":
            return datetime.datetime.strptime(data.split(" ")[0], '%Y:%m:%d').strftime('%A') + ", " + data
    return 'unknown'

def getBrgList(requested:str) -> list:
    list = []
    for c in requested.replace("rgba(","").replace(")","").split(","):
        list.append(int(c))
    list.pop(3)
    list = swapList(list,0,2)
    logger.info('list %s',list)
    return list

def swapList(list:list,i,n)->list:
    list[i], list[n] = list[n], list[i]
    return list

def writeBorder(virat_img,top,bottom,left,right,rgbList,path):
    borderoutput = cv2.copyMakeBorder(
            virat_img,
            top,
            bottom,
            left,
            right,
            cv2.BORDER_CONSTANT,
            value=rgbList,
        )
    cv2.imwrite(path, borderoutput)
def getRgba(value,default):
    if('rgba' not in value):
        return default
    return value
# fullexif
# 'LensModel': 'EF50mm f/1.8 STM'
# 'DateTime': '2019:03:02 15:21:27'

def convert_heic_to_jpeg(origin_dir,converted_dir):
        filenames = os.listdir(origin_dir)
        filenames_matched = [re.search("\.HEIC$|\.heic$", filename) for filename in filenames]

        # Extract files of interest
        HEIC_files = []
        for index, filename in enumerate(filenames_matched):
                if filename:
                        HEIC_files.append(filenames[index])

        # Convert files to jpg while keeping the timestamp
        for filename in HEIC_files:
                image = Image.open(origin_dir + "/" + filename)
                image_exif = image.getexif()
                if image_exif:
                        # Make a map with tag names and grab the datetime
                        exif = { ExifTags.TAGS[k]: v for k, v in image_exif.items() if k in ExifTags.TAGS and type(v) is not bytes }
                        date = datetime.datetime.strptime(exif['DateTime'], '%Y:%m:%d %H:%M:%S')

                        # Load exif data via piexif
                        exif_dict = piexif.load(image.info["exif"])

                        # Update exif data with orientation and datetime
                        exif_dict["0th"][piexif.ImageIFD.DateTime] = date.strftime("%Y:%m:%d %H:%M:%S")
                        exif_dict["0th"][piexif.ImageIFD.Orientation] = 1
                        exif_bytes = piexif.dump(exif_dict)

                        # Save image as jpeg
                        image.save(converted_dir + "/" + os.path.splitext(filename)[0] + ".jpg", "jpeg", exif= exif_bytes)
                else:
                        print(f"Unable to get exif data for {filename}")

        return "ok"
def download(request):
    download_media_path = str(settings.MEDIA_ROOT) + "/download"
    if (request.method == "POST"):
        link = request.POST["ytb_url"]
        print(link)
        ydl_opts = {
            'outtmpl': download_media_path + '/%(title)s.%(ext)s',  # Save path and file name
            'postprocessors': [{  # Post-process to convert to MP3
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',  # Convert to mp3
                'preferredquality': '0',  # '0' means best quality, auto-determined by source
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return render(request,"download.html")
    else:
        return render(request,"download.html")