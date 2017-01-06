import requests
from bs4 import BeautifulSoup

from http.cookiejar import FileCookieJar
from http.cookiejar import LWPCookieJar
from http.cookiejar import MozillaCookieJar

import os

def getBaseSourceURL(markup):
    soup = BeautifulSoup(markup,"html.parser")
    video = soup.find("video")
    source = video.find("source")
    sourceURL = source["src"]
    baseSourceURL = sourceURL.rsplit("/",1)[0]
    return baseSourceURL

def appendPathComponent(base,addition):
    if not base[len(base)-1] == '/':
        base += '/'
    base+=addition
    return base

def downloadTextContent(url,cookies):
    print("downloading text content from "+url)
    resp = requests.get(url,cookies=cookies)
    return resp.text

def downloadContent(url,path,cookies=None):
    print("downloading "+url+" to "+path)
    file = open(path,"wb")
    resp = requests.get(url,stream=True,cookies=cookies)
    file.write(resp.content)
    file.close()

def makeEpisodeURL(episode):
    pageURL = baseURL + episode
    return pageURL

def saveUTF8Text(text,path):
    file = open(path, "wb")
    file.write(text.encode("utf-8"))
    file.close()

def loadUTF8Text(path):
    file = open(path,"rb")
    content = file.read()
    file.close()
    return content.decode("utf-8")

def getFilesFromM3U(m3uContent):
    lines = m3uContent.split("\n")
    filenames = list(filter(lambda l: len(l)>0 and not l[0]=='#',lines))
    return filenames

baseURL = "https://talk.objc.io/episodes/"

def download(episode):
    cookies = MozillaCookieJar(filename=os.getcwd()+'/cookies.txt')
    cookies.load()
    pageContent = downloadTextContent(makeEpisodeURL(episode), cookies=cookies)
    baseSourceURL = getBaseSourceURL(pageContent)
    m3uURL = appendPathComponent(baseSourceURL, '1080p.m3u8')
    m3uContent = downloadTextContent(m3uURL, cookies=cookies)
    tsFiles = getFilesFromM3U(m3uContent)
    print("will download the following chunks: ",tsFiles)
    print("# of chunks: ",len(tsFiles))
    if len(tsFiles)<20:
        print("skipping, probably cookie has expired")
        return

    dir = os.path.join(os.getcwd(),'content',episode)
    os.system('mkdir ' + dir)

    files = os.listdir(dir)
    if len(files) >= len(tsFiles):
        print("skipping already downloaded")
        return

    for tsFile in tsFiles:
        tsFileURL = appendPathComponent(baseSourceURL, tsFile)
        tsFilePath = os.path.join(dir,tsFile)
        downloadContent(tsFileURL, tsFilePath, cookies=cookies)

episodes = []
for i in range(12,31):
    episode="S01E" + '{:02d}'.format(i)
    episodes.append(episode)
print(episodes)
for episode in episodes:
    download(episode)
    pass

#gluing all episodes together
#mkdir videos
#cd content
#for episode in `ls`; do echo "cat $episode/* > ../videos/$episode.m2ts"; done