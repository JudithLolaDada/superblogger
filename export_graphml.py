import pymongo
import pygraphml

mutual_only = True

# MongoDB
db = pymongo.MongoClient('127.0.0.1', 27017).superblogger

g = pygraphml.Graph()

users = dict()
nodes = dict()
for user in db.users.find({'counts.followed_by': {'$gte': 1000000}, 'follows': {'$exists': True}}):
    users[user['id']] = user    

def add_node(user):
    if user['id'] in nodes:
        return
    nodes[user['id']] = g.add_node(user['username'])
    nodes[user['id']]['follows'] = user['counts']['follows']
    nodes[user['id']]['followed_by'] = user['counts']['followed_by']

for user in db.users.find({'counts.followed_by': {'$gte': 1000000}, 'follows': {'$exists': True}}):
    for followed_user_id in user['follows']:
        if followed_user_id in users and (not mutual_only or user['id'] in users[followed_user_id]['follows']):
            add_node(user)
            add_node(users[followed_user_id]) 
            g.add_edge(nodes[user['id']], nodes[followed_user_id], directed=(not mutual_only))


parser = pygraphml.GraphMLParser()
parser.write(g, "superbloggers"+("_mutual_only" if mutual_only else "")+".graphml")
