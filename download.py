# python3 script
# put your cookie.txt next to the script and launch it from that working dir
#

import requests
from bs4 import BeautifulSoup
import os
import sys
from GoogleDriveWrapper import Folder
from cookies import loadCookies
import subprocess
from pathlib import PurePath

CHUNKS_DIR = 'content'
VIDEOS_DIR = 'videos'

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

class Episode:
    def __init__(self,baseURL,relativeURL):
        self.baseURL = baseURL
        self.relativeURL = relativeURL
        self.fullName = self.getFullName()
        self.shortName = self.getShortName()
        self.ext = 'mp4'
        self.gdriveUpload = False

    def __str__(self):
        return "Episode: " + self.fullName

    def __repr__(self):
        return self.__str__()

    def getFullName(self):
        components = self.relativeURL.split('/')
        return components[len(components)-1]

    def getShortName(self):
        components = self.fullName.split('-')
        return components[0]

    def makeEpisodePageURL(self):
        pageURL = appendPathComponent(self.baseURL,self.fullName)
        return pageURL

    def getFileName(self, name):
        return name + '.' + self.ext

    def getVideoDir(self):
        return os.path.join(os.getcwd(), VIDEOS_DIR)

    def getVideoFilePath(self):
        fullFileName = self.getFileName(self.fullName)
        fullFileName = os.path.join(self.getVideoDir(), fullFileName)
        return fullFileName

    def renameExistingIfNeeded(self):
        fullFileName = self.getFileName(self.fullName)
        fullFilePath = self.getVideoFilePath()
        if os.path.exists(fullFilePath):
            return
        shortFileName = self.getFileName(self.shortName)
        shortFilePath = os.path.join(os.getcwd(), VIDEOS_DIR, shortFileName)
        if os.path.exists(shortFilePath):
            print("renaming " + shortFileName + " to " + fullFileName)
            os.rename(shortFilePath,fullFilePath)

    def isDownloaded(self):
        return os.path.exists(self.getVideoFilePath())

    def gdriveUploadIfNeeded(self):
        if self.gdriveUpload:
            folder = Folder(PurePath('Screencasts/SwiftTalk'))
            file = folder.fileForName(self.fullName)
            if file == None:
                print('uploading to google drive')
                folder.upload(self.getVideoFilePath())
            else:
                print('already uploaded')

    def leaveEmptyFile(self):
        filepath = self.getVideoFilePath()
        os.remove(filepath)
        fd = os.open(filepath, flags=os.O_CREAT, mode=0o644)
        os.close(fd)

    def download(self,cookies):
        print("Downloading", self)
        url = self.makeEpisodePageURL()
        if self.isDownloaded():
            print(self.fullName + ' is already downloaded')
        else:
            subprocess.run(['youtube-dl',
                            '--cookies',
                            'cookies.txt',
                            '--output',
                            self.getVideoFilePath(),
                            '--no-check-certificate',
                            url])

        self.gdriveUploadIfNeeded()
        self.leaveEmptyFile() # so that we have a mark that we downloaded it


def saveUTF8Text(text,path):
    file = open(path, "wb")
    file.write(text.encode("utf-8"))
    file.close()

def loadUTF8Text(path):
    file = open(path,"rb")
    content = file.read()
    file.close()
    return content.decode("utf-8")

def parseEpisodes(baseURL,cookies):
    episodesPage = downloadTextContent(baseURL,cookies)
    soup = BeautifulSoup(episodesPage, "html.parser")
    episodes = []
    for h3 in soup.find_all('h3'):
        a = h3.find('a')
        if a is None:
            return None
        relativeURL = a['href']
        episode = Episode(baseURL,relativeURL)
        episodes.append(episode)
    return episodes

def main():
    baseURL = "https://talk.objc.io/episodes/"
    cookieFileName = os.path.join(os.getcwd(), 'cookies.txt')
    cookies = loadCookies(cookieFileName)
    episodes = parseEpisodes(baseURL, cookies)

    if episodes is None or len(episodes) == 0:
        print("Error parsing episodes, check your cookies")
        return

# TODO: use some nice argument parsing lib, like getopt
    if '--gdrive-upload' in sys.argv:
        for episode in episodes:
            episode.gdriveUpload = True

    if '--last' in sys.argv or '--latest' in sys.argv:
        print("Downloading last episode only")
        episodes[0].download(cookies)
    elif '-e' in sys.argv:
        argInd = sys.argv.index('-e')
        ep = sys.argv[argInd + 1]
        print("Downloading episode",ep)
        for episode in episodes:
            if ep in episode.fullName:
                episode.download(cookies)
                break
    else:
        ep = "some giberish which can't be part of an episode name"
        if '--until' in sys.argv:
            argInd = sys.argv.index('--until')
            ep = sys.argv[argInd + 1]
        for episode in episodes:
            if ep in episode.fullName:
                break
            episode.download(cookies)


if __name__ == "__main__":
    main()
