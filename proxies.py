import random

# Source: https://www.sslproxies.org/

proxies = """
177.37.240.52:8080
115.75.1.184:8118
208.80.28.208:8080
51.159.26.44:3128
103.121.215.208:3127
181.30.60.147:8080
41.217.219.53:31398
213.230.69.33:8080
79.99.18.86:3128
69.63.170.74:3128
103.152.5.80:8080
187.94.16.59:39665
118.27.28.45:3128
18.135.32.174:80
154.72.204.122:8080
78.39.136.179:8080
60.246.7.4:8080
139.59.127.21:8118
43.225.67.35:53905
124.41.213.122:46646
118.27.26.70:3128
51.75.147.44:3128
185.156.172.122:3128
195.25.19.4:8080
79.151.172.218:8080
103.241.227.110:6666
192.140.42.81:47277
109.105.205.232:59152
118.175.207.180:40017
193.34.93.221:53805
118.173.233.149:45160
193.200.151.69:48241
62.23.15.92:3128
118.27.1.112:3128
1.0.183.111:8080
187.45.123.137:36559
14.207.58.3:3128
1.2.169.101:47477
124.41.211.196:31120
41.79.33.170:8080
62.210.69.176:5566
113.53.29.218:33885
181.30.60.148:8080
144.202.29.211:3128
51.75.147.41:3128
209.124.56.54:3128
91.192.2.168:53281
217.219.31.210:38073
142.93.245.236:31583
94.30.97.245:80
36.67.24.109:31255
91.245.72.125:8080
1.10.186.35:37235
176.56.107.198:32439
81.174.11.227:47324
37.17.38.196:53281
109.162.254.10:8080
102.67.19.132:8080
116.90.229.186:35561
189.204.242.178:8080
103.12.161.38:55443
92.86.10.42:42658
161.202.226.194:80
8.209.81.93:3128
176.197.95.2:3128
51.178.49.77:3132
45.9.229.28:3128
181.198.97.241:30072
182.52.90.117:45535
36.89.228.201:45286
201.49.58.234:80
198.50.163.192:3129
37.79.254.152:3128
103.209.64.19:6666
83.103.193.74:13192
180.179.98.22:3128
181.129.2.29:8080
202.75.97.82:47009
202.51.118.34:55443
89.208.35.79:60358
202.169.244.178:8181
118.172.51.84:43147
114.57.49.66:53281
187.109.114.112:48542
89.36.195.238:35328
148.101.21.182:999
114.5.35.98:38554
103.113.17.94:8080
45.235.216.112:8080
43.252.237.84:8080
5.59.142.97:8080
178.128.189.193:3128
5.141.244.28:8080
180.180.156.15:43100
118.99.100.30:8080
78.140.201.254:11335
201.193.180.14:35746
182.52.90.43:33326
118.174.234.21:43195
103.253.27.108:80""".split()[1:]


def get_proxy():
    return random.choice(proxies)
