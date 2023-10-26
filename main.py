import json
import time
import sys
import requests

from datetime import datetime, timezone
from seleniumwire import webdriver

SLEEP_TIME = 60
NO_API_SLEEP_TIME = 60
CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver'
WEBHOOK_URL = ""


def seconds_to_text(secs):
    days = secs // 86400
    hours = (secs - days * 86400) // 3600
    minutes = (secs - days * 86400 - hours * 3600) // 60
    seconds = secs - days * 86400 - hours * 3600 - minutes * 60

    if days:
        listed_time = ("{0} day{1} ago ".format(int(days), "s" if days != 1 else ""))
    elif hours:
        listed_time = ("{0} hour{1} ago ".format(int(hours), "s" if hours != 1 else ""))
    elif minutes:
        listed_time = ("{0} minute{1} ago ".format(int(minutes), "s" if minutes != 1 else ""))
    elif seconds:
        listed_time = ("{0} second{1} ago ".format(int(seconds), "s" if seconds != 1 else ""))

    return listed_time


def check_listings(code):
    link = 'https://www.pathofexile.com/trade/search/Expedition/' + code

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=options)

    items_found = []
    while True:
        driver.get(link)

        try:
            request = driver.wait_for_request('/api/trade/fetch/', timeout=10)
            driver.get(request.url)
            content = driver.find_element_by_tag_name('pre').text
            parsed_json = json.loads(content)

            fields = []
            total = 0
            for result in parsed_json['result']:
                if result['id'] not in items_found and total < 8:
                    time_listed = datetime.strptime(result['listing']['indexed'], '%Y-%m-%dT%H:%M:%S%z')
                    seconds = ((datetime.now(timezone.utc) - time_listed).total_seconds())
                    difference = seconds_to_text(seconds)
                    price_value = str(result['listing']['price']['amount']) + " " + result['listing']['price']['currency']

                    mods = ""
                    try:
                        if result['item']['implicitMods']:
                            implicit_mods = result['item']['implicitMods']
                            for mod in implicit_mods:
                                if mod == implicit_mods[-1]:
                                    mods += ("__" + mod + "__\n")
                                else:
                                    mods += mod + "\n"
                    except:
                        pass

                    try:
                        if result['item']['explicitMods']:
                            explicit_mods = result['item']['explicitMods']
                            for mod in explicit_mods:
                                mods += (mod + "\n")
                    except:
                        pass

                    socket_string = ""
                    group = 0
                    try:
                        for socket in result['item']['sockets']:
                            if socket_string == "":
                                socket_string += socket['sColour']
                            else:
                                if socket['group'] == group:
                                    socket_string += "-" + socket['sColour']
                                else:
                                    group += 1
                                    socket_string += " " + socket['sColour']
                    except:
                        pass

                    whisper = '```' + result['listing']['whisper'] + '```'

                    corrupted = ""
                    try:
                        if result['item']['corrupted']:
                            corrupted = "(CORRUPTED)"
                    except:
                        pass

                    fields.append({
                        "name": result['item']['name'] + " " + result['item']['baseType'] + " " + corrupted,
                         #"value": mods + "\n" + whisper + "\nListed " + difference + "\n",
                        "value": mods + "\n" + "Listed " + difference + "\n\n",
                        "inline": True
                    })

                    if socket_string:
                        fields.append({
                            "name": "SOCKETS",
                            "value": socket_string,
                            "inline": True
                        })
                    else:
                        fields.append({
                            "name": "\u200B",
                            "value": "\u200B",
                            "inline": True
                        })

                    fields.append({
                        "name": "PRICE",
                        "value": price_value,
                        "inline": True
                    })

                    items_found.append(result['id'])
                    total += 1

            fields.append({
                "name": "\u200B",
                "value": f"[TRADE LINK]({link})",
                "inline": False
            })

            body = {
                "embeds": [
                    {
                        "title": "ITEM(s) FOUND",
                        "fields": fields,
                    }
                ]
            }

            if total > 0:
                req = requests.post(WEBHOOK_URL, json=body)
                print(f"found items. retrying in {SLEEP_TIME} seconds")
                time.sleep(SLEEP_TIME)
            else:
                print(f"did not find items. retrying in {SLEEP_TIME} seconds")
                time.sleep(SLEEP_TIME)
        except:
            print(f"could not fetch API link. retrying in {NO_API_SLEEP_TIME} seconds")
            time.sleep(NO_API_SLEEP_TIME)


if __name__ == '__main__':
    code = str(sys.argv[1])
    check_listings(code)