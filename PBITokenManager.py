import PyChromeDevTools
import time
import os
import Settings
import json


if not "NO_PROXY" in os.environ.keys():
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
else:
    if "localhost" not in os.environ["NO_PROXY"]:
        os.environ["NO_PROXY"] += ",localhost"
    if "127.0.0.1" not in os.environ["NO_PROXY"]:
        os.environ["NO_PROXY"] += ",127.0.0.1"

chrome=PyChromeDevTools.ChromeInterface()
chrome.Network.enable()
chrome.Page.enable()


bearer_token=False
bearer_token_string=""
mwc_token=False
mwc_token_string=""
api_url=False
api_url_string=""


def extract_tokens(message):
    global bearer_token, bearer_token_string, mwc_token, mwc_token_string, api_url, api_url_string
    if not api_url:
        if "method" in message and message["method"] in ["Network.responseReceived"]:
            if "response" in message["params"]:
                api_url_string = message["params"]["response"]["url"]
                if api_url_string[120:]=="/workloads/QES/QueryExecutionService/automatic/public/query" and "/webapi/" in api_url_string:
                    Settings.api_url=api_url_string
                    api_url=True
                    #print(Settings.api_url)

    if not bearer_token or not mwc_token:
        if "method" in message and message["method"] in ["Network.requestWillBeSentExtraInfo", "Network.requestWillBeSent"]:
            if "headers" in message["params"]:
                if "Authorization" in message["params"]["headers"]:
                    request_h=message["params"]["headers"]["Authorization"]
                    if not bearer_token:
                        if str(request_h).startswith("Bearer"):
                            bearer_token=True
                            bearer_token_string = str(request_h)
                            #print(bearer_token_string)
                            Settings.br_token = bearer_token_string
                            Settings.header = {"Content-Type": "application/json; charset=UTF-8",
                                               "Authorization": Settings.br_token}

                    if not mwc_token:
                        if str(request_h).startswith("MWCToken"):
                            mwc_token = True
                            mwc_token_string = str(request_h)
                            Settings.mwc_token = mwc_token_string
                            #print(Settings.mwc_token)
                            Settings.header = {"Content-Type": "application/json; charset=UTF-8",
                                               "Authorization": Settings.mwc_token}




#event, messages =chrome.wait_event("Page.frameStoppedLoading", timeout=60)

def gettoken():
    global bearer_token, bearer_token_string, mwc_token, mwc_token_string, api_url, api_url_string
    bearer_token=False
    mwc_token=False
    api_url=False

    Settings.mwc_token=""
    Settings.br_token=""
    Settings.api_url =""

    chrome.Page.navigate(url="https://www.google.ca/")
    time.sleep(2)

    chrome.Page.navigate(
        url=Settings.pbi_url)
    time.sleep(5)

    while not (bearer_token and mwc_token and api_url):
        messages=chrome.wait_message()
        if messages is not None:
            #print(messages)
            #with open(f'./msgs.log', 'a', encoding='utf-8-sig') as f:
            #    f.write(json.dumps(messages))
            extract_tokens(messages)

    print(Settings.mwc_token)
    print(bearer_token_string)
    print(Settings.api_url)

    return True



#print(bearer_token_string[7:])
#print(mwc_token_string[9:])

#bearer_token
#token

#mwc_token
#token