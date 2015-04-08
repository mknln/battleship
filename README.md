sudo pip install https://github.com/mitsuhiko/flask/tarball/master  
sudo pip install flask-mysql  

To run:  
1. Set up database info in `config`  
2. Run `create_database.sh` (first time only)  
3. `./run.sh`  

A typical set of requests looks like this (in case it helps figuring out how to run it):  
```
 * Running on http://0.0.0.0:5000/
 127.0.0.1 - - [08/Apr/2015 00:12:25] "GET /api/game/create HTTP/1.1" 200 -
 192.168.1.112 - - [08/Apr/2015 00:12:30] "GET /api/game/list HTTP/1.1" 200 -
 192.168.1.112 - - [08/Apr/2015 00:12:35] "GET /api/game/join/4 HTTP/1.1" 400 -
 192.168.1.112 - - [08/Apr/2015 00:12:40] "GET /api/game/join/4 HTTP/1.1" 200 -
 192.168.1.112 - - [08/Apr/2015 00:12:41] "GET /api/game/join/4 HTTP/1.1" 400 -
 127.0.0.1 - - [08/Apr/2015 00:12:59] "GET /api/game/clickHandler/4/5 HTTP/1.1" 404 -
 127.0.0.1 - - [08/Apr/2015 00:13:03] "GET /api/game/4/clickHandler/4/5 HTTP/1.1" 200 -
 127.0.0.1 - - [08/Apr/2015 00:13:05] "GET /api/game/4/clickHandler/4/5 HTTP/1.1" 401 -
 192.168.1.112 - - [08/Apr/2015 00:13:13] "GET /api/game/clickHandler/7/2 HTTP/1.1" 404 -
 192.168.1.112 - - [08/Apr/2015 00:13:16] "GET /api/game/4/clickHandler/7/2 HTTP/1.1" 200 -
 192.168.1.112 - - [08/Apr/2015 00:13:17] "GET /api/game/4/clickHandler/7/2 HTTP/1.1" 401 -
 127.0.0.1 - - [08/Apr/2015 00:13:22] "GET /api/game/4/clickHandler/4/5 HTTP/1.1" 400 -
 127.0.0.1 - - [08/Apr/2015 00:13:24] "GET /api/game/4/clickHandler/4/6 HTTP/1.1" 200 -
```
