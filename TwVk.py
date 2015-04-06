#!/usr/bin/env python

import tweepy, json, requests, logging, time

#Twitter tokens
consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""

#start with @
twitter_username = ''

#VK tokens
#url for token: https://oauth.vk.com/authorize?client_id={appId}&scope=wall,photos,offline&redirect_uri=http://oauth.vk.com/blank.html&display=page&response_type=token
vkToken = ""


#Main method
def main():
    try:
        logging.basicConfig(format = '%(asctime)s.%(msecs)d %(levelname)s %(message)s',
                            datefmt = '%Y-%m-%d %H:%M:%S',
                            filename = 'TwVk.log',
                            level = logging.INFO)
        logging.info('Script started')

        #authorization in twitter
        url = "https://userstream.twitter.com/1.1/user.json"
        param = {"with":"user"}
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_key, access_secret)
        logging.info('Twitter authorization successful')

        #getting tweets
        savefile = open('TwVkStatus.txt','r');
        lasttweet = savefile.readline()
        savefile.close()
        twApi = tweepy.API(auth)

        while True:
            savefile = open('TwVkStatus.txt','rw+');
            tweets = twApi.user_timeline(since_id=lasttweet);
            for tweet in reversed(tweets):
                handleTweet(tweet.__dict__)
                logging.info('Tweet ID: '+str(tweet.id))
                lasttweet = str(tweet.id)
                savefile.seek(0,0)
                savefile.write(lasttweet)
            savefile.close()
            time.sleep(60)
            logging.info('Tic-tac')

    except:
        logging.exception('Main exception')

#Method handling tweet
def handleTweet(tweet):
    logging.info('Starting handleTweet')
    #get tweet text
    text = tweet["text"]
    logging.info('Tweet text: ' + text)
    #check for answer, retweet or mention
    if not text.startswith('@') and not twitter_username in text:
        #get urls in tweet
        urls = tweet["entities"]["urls"]
        attachments = ""

        if 1 <= len(urls):

            first_url = urls[0]["expanded_url"]

            hosts = ['youtu.be','vimeo','youtube']
            exts = ['.jpg','.png','.jpeg']

            if any(s in first_url for s in hosts):
                attachments = uploadVideo(first_url)
                text = text.replace(first_url," ")
            elif any(s in first_url for s in exts):
                attachments = uploadPhoto(first_url)
            else:
                attachments = first_url

        #replace shortened urls
        for url in urls:
            text = text.replace(url["url"], url["expanded_url"])

        text = text.strip()

        logging.info('Tweet text with urls: ' + text)

        #if photo is attached - remove it and upload to VK
        if "media" in tweet["entities"]:
            photo = tweet["entities"]["media"][0]
            logging.info('Photo found. Url: ' + photo["media_url"])
            text = text.replace(photo["url"], "")
            attachments = uploadPhoto(photo["media_url"])

        logging.info('Attachments: ' + attachments)

        #post to VK and attach photo ID
        vkMethod('wall.post', {'message': text,'attachments':attachments})
        logging.info('Posted to VK')

    else:
        logging.info('Skipping tweet')
        

def uploadVideo(fileUrl):

    tmp = vkMethod('video.save',{'is_private':'1','link':fileUrl})
    logging.info('VK punched with %s' % fileUrl)

    uploadUrl = tmp['response']['upload_url']
    vid = tmp['response']['vid']
    oid = tmp['response']['owner_id']
    logging.info('VK answered with video_id %s' % vid)

    r = requests.get(uploadUrl).json()
    logging.info('Poked VK with upload_url and get these: %s' % r)

    if r['response'] == 1:
        attachments = 'video%(oid)s_%(vid)s' % {'oid':oid,'vid':vid}
        logging.info('Posting %s' % attachments)

        return attachments


def uploadPhoto(fileUrl):
    logging.info('Start uploading photo')
    #get url for uploading photo
    response = vkMethod('photos.getWallUploadServer')
    uploadUrl = response['response']['upload_url']
    logging.info('Get upload url: ' + uploadUrl)

    #saving photo locally    
    with open('temp.jpg','wb') as tempfile:
        photo = requests.get(fileUrl, stream=True)
        for block in photo.iter_content(1024):
            tempfile.write(block)
    logging.info('Photo saved on local drive')

    #uploading photo to VK
    files = {'photo': open('temp.jpg','rb')}
    response = requests.post(uploadUrl, files = files).json()
    logging.info('Photo uploaded')
    #add photo in wall album
    response = vkMethod('photos.saveWallPhoto', response)
    logging.info('Photo saved in wall album ')
    #return photo ID
    return response['response'][0]['id']

#Common VK API method
def vkMethod(method, data={}):
    url = 'https://api.vk.com/method/%s.json' % (method)
    data.update({'access_token': vkToken})

    response = requests.post(url, data)

    if 'error' in response:
        error = response['error']
        logging.error('API: error (%s)' % (error['error_msg']))

    return response.json()


main()