import pymongo
import pygraphml

# MongoDB
db = pymongo.MongoClient('127.0.0.1', 27017).superblogger

g = pygraphml.Graph()

nodes = dict()
for user in db.users.find({'counts.followed_by': {'$gte': 1000000}, 'follows': {'$exists': True}}):
    nodes[user['id']] = g.add_node(user['username'])
    nodes[user['id']]['follows'] = user['counts']['follows']
    nodes[user['id']]['followed_by'] = user['counts']['followed_by']
    
for user in db.users.find({'counts.followed_by': {'$gte': 1000000}, 'follows': {'$exists': True}}):
    for followed_user_id in user['follows']:
        if followed_user_id in nodes:
            g.add_edge(nodes[user['id']], nodes[followed_user_id], directed=True)


parser = pygraphml.GraphMLParser()
parser.write(g, "superbloggers.graphml")