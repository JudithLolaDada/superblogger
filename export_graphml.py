import pymongo
import pygraphml

mutual_only = True

# MongoDB
db = pymongo.MongoClient('127.0.0.1', 27017).superblogger

g = pygraphml.Graph()

users = dict()
nodes = dict()
for user in db.users.find({'counts.followed_by': {'$gte': 1000000}, 'follows': {'$exists': True}}):
    nodes[user['id']] = g.add_node(user['username'])
    nodes[user['id']]['follows'] = user['counts']['follows']
    nodes[user['id']]['followed_by'] = user['counts']['followed_by']
    users[user['id']] = user    

for user in db.users.find({'counts.followed_by': {'$gte': 1000000}, 'follows': {'$exists': True}}):
    for followed_user_id in user['follows']:
        if followed_user_id in nodes and (not mutual_only or user['id'] in users[followed_user_id]['follows']):
            g.add_edge(nodes[user['id']], nodes[followed_user_id], directed=(not mutual_only))


parser = pygraphml.GraphMLParser()
parser.write(g, "superbloggers"+("_mutual_only" if mutual_only else "")+".graphml")
