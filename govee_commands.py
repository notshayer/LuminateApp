import yaml
import requests
from time import sleep
import json

GOVEE_SESSION = requests.Session()
GOVEE_SESSION.verify = False

with open('app_ref.yaml', "r") as f:
    app_data = yaml.safe_load(f)
GOVEE_API_KEY = app_data['GOVEE_API_KEY']
HEADER = {"Govee-API-Key": GOVEE_API_KEY}
BASE_URL = "https://developer-api.govee.com/"
CMD_URLS = {
    "get_device_infos" : "v1/devices",
    "set_device"      : "v1/devices/control"
}

GOVEE_DEFAULT_CMD_BODY = """ "cmd":{{"name":"{0}", "value":{1}}}"""


## Follow 
GOVEE_LIGHT_CMDS = {
    "turn": ("on", "off"),
    "brightness": (0, 100),
    "color": """{{"r":{0}, "g":{1}, "b":{2}}}""" 
}

CMD_BODY = '"device":"{0}", "model": "{1}",'



CMD_DATA_KEYS = {
    "get_device_infos" : ["code", "message", "data"],
}

## Filled 
GOVEE_LIGHTS = {
    
}

def process_payload(input_payload):
    payload = None
    if type(input_payload) == list:
        set_key = input_payload[0]
        values = input_payload[1]
        if set_key in GOVEE_LIGHT_CMDS.keys():
            if set_key == "color":
                if len(values) == 3:
                    rgb_values_dict = GOVEE_LIGHT_CMDS['color'].format(*values)
                    payload = GOVEE_DEFAULT_CMD_BODY.format(*[set_key, rgb_values_dict])
                    # print(payload)
            else:
                if set_key == "brightness":
                    payload = GOVEE_DEFAULT_CMD_BODY.format(input_payload[0], str(input_payload[1]))
                else:
                    payload = GOVEE_DEFAULT_CMD_BODY.format(input_payload[0], '"'+input_payload[1]+'"')
                # print(payload)
                
        else:
            print("invalid input_payload[0]: should be {0}, {1}, or {2}".format(GOVEE_LIGHT_CMDS.keys()))
            
    return payload

def call_govee_api_cmd(cmd_key, device_info = None, payload = None):
    url = BASE_URL + CMD_URLS[cmd_key]
    s = GOVEE_SESSION
    if 'get' in cmd_key:
        cmd_ptr = s.get
    elif 'set' in cmd_key:
        cmd_ptr = s.put
        if payload != None and device_info != None:
            cmd_body_start = "{" + CMD_BODY.format(*device_info)
            # print(cmd_body_start)
            payload = cmd_body_start + process_payload(payload) + "}"
            print(payload)
        else:
            print("error in input payload or device info: {}, {}".format(payload, device_info))
        payload = json.loads(payload)
    print(payload)
    req = cmd_ptr(url, headers=HEADER, json=payload, verify=False)
    return req.json()
    
def get_govee_lights_info():
    cmd_key = "get_device_infos"
    result = call_govee_api_cmd(cmd_key)
    return result
    
def set_govee_light(mac_address, model_name, light_cmd_key, value):
    device_info = [mac_address, model_name]
    payload_in = [light_cmd_key, value]
    result = call_govee_api_cmd("set_device", device_info=device_info, payload=payload_in)
    return result
    
def process_device_list(get_lights_data_response):
    global GOVEE_LIGHTS
    lights_data = get_lights_data_response['data']['devices']
    for light in lights_data:
        user_given_name = light["deviceName"]
        if light['controllable'] == True:
            ## values are stored as [MAC_ADDRESS, MODEL]
            GOVEE_LIGHTS[user_given_name] = [light['device'], light['model']]
        else:
            #TODO: maybe do something else here
            GOVEE_LIGHTS[user_given_name] = [light['device'], light['model']]
            
def get_lights_lookup():
    res = get_govee_lights_info()
    process_device_list(res)
    for light in GOVEE_LIGHTS.values():
        print(light)
        # exit()
        res = set_govee_light(light[0], light[1], "turn", "on")
        print(res)
        res = set_govee_light(light[0], light[1], "brightness", 50)
        print(res)
        res = set_govee_light(light[0], light[1], "color", [0, 230, 255])
        print(res)
        
    