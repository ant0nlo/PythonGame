# server/config.py

HOST = '127.0.0.1'
PORT = 5555
MAX_CLIENTS = 10
UPDATE_INTERVAL = 0.05  # seconds between state updates

RECONNECT_ATTEMPTS = 3
RECONNECT_DELAY = 2

hardcoded_layout = [
            [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8],
            [8,0,0,0,0,4,0,0,12,0,0,0,4,0,0,4,0,0,0,8],
            [8,0,1,1,0,4,0,7,0,0,12,0,0,7,0,4,0,3,0,8],
            [8,0,1,1,0,4,0,0,0,0,0,0,0,0,0,4,0,3,0,8],
            [8,0,0,1,0,0,0,0,5,5,0,5,5,0,0,0,0,3,0,8],
            [8,0,12,0,0,0,7,0,0,0,0,0,0,0,0,0,0,0,0,8],
            [8,0,10,10,10,0,0,7,0,0,12,0,0,7,0,0,10,10,10,8],
            [8,0,10,10,10,0,0,0,0,0,0,0,0,0,0,0,10,10,10,8],
            [8,0,0,0,0,0,0,0,4,0,4,0,0,0,0,0,0,0,0,8],
            [8,0,0,0,0,5,0,0,0,0,0,0,0,0,6,0,0,0,0,8],
            [8,0,0,7,0,0,0,4,0,0,0,0,4,0,0,0,0,0,0,8],
            [8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,12,0,0,0,8],
            [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
        ]
