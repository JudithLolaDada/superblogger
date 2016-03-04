import urllib.request
import json
import pprint
import pymongo
import subprocess
import time
import os

crawler = subprocess.check_output('hostname').decode('utf-8').strip()

# Instagram API
access_token = os.environ['ACCESS_TOKEN']
seed_user_ids = ["208560325", "247944034"] #Kloe, Beyoncé

# MongoDB 
db = pymongo.MongoClient('127.0.0.1', 27017).superblogger
db = pymongo.MongoClient(os.environ.get('MONGODB') or "mongodb://127.0.0.1").superblogger

# Fetches the a JSON endpoint at `url`.
# If the API Rate Limit is hit, sleeps and retries.
def get_json(url):
    while True:
        try:
            response = urllib.request.urlopen(url)
            response_body = response.read().decode('utf-8')
            print(response.info()['X-Ratelimit-Remaining']) 
            return json.loads(response_body)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("Rate limit hit, waiting five minutes", e.read())
                time.sleep(60*5)
                continue
            if e.code == 400:
                error_response = e.read().decode('utf-8')
                error_json = json.loads(error_response)
                if 'meta' in error_json and error_json['meta']['error_type'] == 'APINotAllowedError':
                    #print("A private user was found!😡");
                    return None
            raise e
    
# Fetch a user and each user of its follows list.
#
# A user that has been visited by this function will have the key 
# `follows` present in the document.
# If a user has only been visited through the iterations of the 
# follows list of this function, the `follows` key is not present
#
# We keep a temporary key `_inProgress`, which indicates if the user
# is currently being processed by a crawler, i.e. its follows list is 
# followed and their users are downloaded
#
def fetch_user(user_id):
    user_id = str(user_id)
    
    if db.users.count({'id': user_id, 'follows': {'$exists': False}}) == 0:
        return
    
    print("Fetching user", user_id)
    
    response_data = get_json("https://api.instagram.com/v1/users/"+user_id+"?access_token=" + access_token)
    if response_data == None:
        db.users.update_one(
            {'id': user_id}, 
            {'$set': {'_private': True}})
        return
    
    user = response_data['data']
    user['follows'] = list()
    user['_inProgress'] = True
    user['_crawler'] = crawler
    
    db.users.update_one(
        {'id': response_data['data']['id']}, 
        {'$set': response_data['data']}, 
        upsert=True)
    
    url = "https://api.instagram.com/v1/users/"+user_id+"/follows?access_token=" + access_token
    while url != None:
        response_data = get_json(url)
        
        for followed_user in response_data['data']:
            # Save in follows array of initial user
            db.users.update_one(
                {'id': user_id},
                {'$addToSet': {'follows': str(followed_user['id'])}})
                
            # Save user 
            if db.users.count({'id': str(followed_user['id'])}) == 0:
                response_data_details = get_json("https://api.instagram.com/v1/users/"+str(followed_user['id'])+"?access_token=" + access_token)
                if response_data_details != None:
                    followed_user_details = response_data_details['data']
                    followed_user_details['id'] = str(followed_user_details['id'])
                    followed_user_details['_crawler'] = crawler
                    
                    db.users.update_one(
                        {'id': str(followed_user_details['id'])}, 
                        {'$set': followed_user_details}, 
                        upsert=True)
                else:
                    followed_user['_private'] = True
                    db.users.update_one(
                        {'id': str(followed_user['id'])}, 
                        {'$set': followed_user}, 
                        upsert=True)
                
        if 'pagination' in response_data and 'next_url' in response_data['pagination']:
            url = response_data['pagination']['next_url']
        else:
            url = None
       
    db.users.update_one(
        {'id': user_id}, 
        {'$set': {'_inProgress': False}}, 
        upsert=True)


# Initialization
print("This is ", crawler)
print("Deleted", db.users.delete_many({'_crawler': crawler, '_inProgress': True}).deleted_count, "users, which were not fully processed")
fetch_user(seed_user_ids[0]) # TODO Randomize

# Loop until there are no users in the database any more that satisfy the following conditions
# FollowedBy > 1M and never crawled.
while True:
    next_user = db.users.find_one({'counts.followed_by': {'$gte': 1000*1000}, 'follows': {'$exists': False}, '_private': None})
    if next_user == None:
        break
    else:
        fetch_user(next_user['id'])
        
print("If we get here... I'm like winning!")
