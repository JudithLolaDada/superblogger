# Superbloggers
## Starting the crawler:
1. Make sure the database is running. To start execute "./mongod", or right-click on mongod in the file browser and select run.
2. Start the crawler, by opening crawler.py and press "Run". Make sure only one instance is running.

## When running for the first time, create MongoDB indexes:  
`> db.users.createIndex({id: 1})`  
`> db.users.createIndex({'counts.followed_by': 1})`  
`> db.users.createIndex({'counts.followeds': 1})`

## ToDo
* Send E-Mail on Error
* Optimize Output (Rate Limit)
* Multi Crawler
