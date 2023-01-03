import base64
import os
import urllib3
from urllib import request, parse
import json

from variables import config

TWILIO_SMS_URL = "https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json"
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")


def message_body():
    MY_LAT = config.MY_LAT
    MY_LON = config.MY_LON
    api_key = config.api_key
    parameters = {
        "lat": MY_LAT,
        "lon": MY_LON,
        "exclude": "current,minutely,daily",
        "appid": api_key
    }

    http = urllib3.PoolManager()
    r = http.request('GET',
                     f"https://api.openweathermap.org/data/2.5/onecall?lat={MY_LAT}&lon={MY_LON}&appid={api_key}")

    weather_data = json.loads(r.data.decode('utf-8'))

    hourly_weather = weather_data["hourly"][:12]
    first_twelve = []

    for hour_data in hourly_weather:
        first_twelve.append(hour_data["weather"][0]["id"])

    will_rain = False
    print(first_twelve)
    for i in first_twelve:
        if int(i) < 700:
            will_rain = True

    if will_rain:
        return "It's going to rain today. Remember to bring an ☂"
    else:
        return "It's sunny today! Consider going outside."

def lambda_handler(event, context):
    to_number = event['To']
    from_number = event['From']
    body = message_body()

    if not TWILIO_ACCOUNT_SID:
        return "Unable to access Twilio Account SID."
    elif not TWILIO_AUTH_TOKEN:
        return "Unable to access Twilio Auth Token."
    elif not to_number:
        return "The function needs a 'To' number in the format +12023351493"
    elif not from_number:
        return "The function needs a 'From' number in the format +19732644156"
    elif not body:
        return "The function needs a 'Body' message to send."

    # insert Twilio Account SID into the REST API URL
    populated_url = TWILIO_SMS_URL.format(TWILIO_ACCOUNT_SID)
    post_params = {"To": to_number, "From": from_number, "Body": body}

    # encode the parameters for Python's urllib
    data = parse.urlencode(post_params).encode()
    req = request.Request(populated_url)

    # add authentication header to request based on Account SID + Auth Token
    authentication = "{}:{}".format(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    base64string = base64.b64encode(authentication.encode('utf-8'))
    req.add_header("Authorization", "Basic %s" % base64string.decode('ascii'))

    try:
        # perform HTTP POST request
        with request.urlopen(req, data) as f:
            print("Twilio returned {}".format(str(f.read().decode('utf-8'))))
    except Exception as e:
        # something went wrong!
        return e

    return "SMS sent successfully!"

