proxies = """
    117.54.120.10:3129
    95.171.6.90:3128
    124.42.7.103:80
    46.101.27.234:8118
    91.135.216.51:53281
    110.170.150.130:8080
    54.223.100.135:33862
    52.57.21.157:80
""".strip().split()

proxies = [p if ':' in p else p + ':80' for p in proxies]

user_agents = """
    Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36
    
""".strip().split('\n')

user_agents = [ua.strip() for ua in user_agents]