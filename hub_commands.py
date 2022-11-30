import yaml
import requests
from time import sleep
import json

HTTPS_SESSION = requests.Session()
HTTPS_SESSION.verify = False
HUB_CMDS = {
    'config'         : "api/0/config",
    'setup'          : 'api/', # POST method
    'get_lights'     : 'clip/v2/resource/device', # GET method
    'get_light_info' : 'clip/v2/resource/light/',  # GET
    'set_light_on'   : 'clip/v2/resource/light/',
    'set_brightness' : 'clip/v2/resource/light/',
    'set_color'      : 'clip/v2/resource/light/'
}
## POST/GET/PUT Methods body/payloads
HUB_CMD_BODYS = {
    'setup' : {"devicetype": "luminate#0000", "generateclientkey":True},
    'set_light_on'         : """{{"on":{{"on":{0}}}}}""",
    'set_brightness'       : """{{"dimming":{{"brightness":{0}}}}}""",
    'set_color'         : """{{"color":{{"xy":{{"x":{0},"y":{1}}}}}}}"""
}

HUB_LIGHT_SET_OPTIONS = {
    0 : 'set_light_on',
    1 : 'set_brightness',
    2 : 'set_color'
} 
API_HEADER = 'hue-application-key:{0}'
USERKEY = None
CLIENTKEY = None

def get_hub_ips():
    info_url = "https://discovery.meethue.com/"
    hubs_info = requests.get(info_url)
    hubs_data = hubs_info.json()
    hub_ips = []
    hub_ids = []
    for hub in hubs_data:
        hub_ips.append(hub['internalipaddress'])
        # hub_ids.append(hub['id'][-6::]) ## referenced in API for usage, may be deprecated?
    return hub_ips
        
try:
    with open('app_ref.yaml') as f:
    # use safe_load instead load
        app_data = yaml.safe_load(f)
    HUB_IPS = app_data['hub_ips']
    HUB_URLS = ["https://{}/".format(i) for i in HUB_IPS]
    try:
        USERKEY   = app_data['username']
        CLIENTKEY = app_data['clientkey']
        SETUP_REQUIRED = 0
    except:
        SETUP_REQUIRED = 1
        print('setup required! Access tokens not found!')
    SELECTED_HUB_URL = HUB_URLS[0]
    # f.close()
except:
    app_data = {}
    hub_ips = get_hub_ips()
    app_data['hub_ips'] = hub_ips
    SETUP_REQUIRED = 1
    f = open('app_ref.yaml', "w")
    yaml.dump(app_data, f)
    HUB_IPS = app_data['hub_ips']
    HUB_URLS = ["https://{}/".format(i) for i in hub_ips]
    SELECTED_HUB_URL = HUB_URLS[0]
    print('setup required!')
    # f.close()

def setup_keys():
    global USERKEY
    global CLIENTKEY
    s = HTTPS_SESSION
    setup_url = SELECTED_HUB_URL + HUB_CMDS['setup']
    setup_data = HUB_CMD_BODYS['setup']
    setup_req = s.post(setup_url, json=setup_data, verify=False)
    response = setup_req.json()
    response_keys = response[0].keys()
    if 'error' in response_keys:
        try:
            while True:
                sleep(5)
                setup_req = s.post(setup_url, json=setup_data, verify=False)
                response = setup_req.json()
                response_keys = response[0].keys()
                if 'error' not in response_keys:
                    break
                else:
                    print(response)
                
        except KeyboardInterrupt:
            print("Setup Blocked!")
    print(response)  
    
    try:
        if 'success' in response[0].keys():
            key_data = response[0]['success']
    except:
        print('Key data lost!')
        
    # try:
    with open('app_ref.yaml', "r") as f:
        app_data = yaml.safe_load(f)
    app_data['username'] = key_data['username']
    app_data['clientkey'] = key_data['clientkey']
    with open('app_ref.yaml', "w") as f:
        yaml.dump(app_data, f)
    USERKEY = app_data['username']
    CLIENTKEY = app_data['clientkey']
    f.close()
    # except:
    #     print('failed to write keys to file')
    return key_data
            

def set_api_key():
    global USERKEY
    global CLIENTKEY
    global API_HEADER
    if SETUP_REQUIRED == 1:
        keys = setup_keys()
    API_HEADER = API_HEADER.format(USERKEY)

def create_light_data_structs(light_data):
    ## Names are given by the user
    ## RIDs are product info that allow API access
    light_names = []
    light_rids  = []
    for light in light_data:
        light_names.append(light['metadata']['name'])
        light_rids.append(light['services'][0]['rid'])
        
    light_data = {
        "names" : light_names,
        "rids"  : light_rids
    }
    #TODO: Break up into rooms?
    return light_data

## Used for all cmds specific to a hub
def call_hub_api_cmd(cmd_key, light_rid = "", payload = None):
    url = SELECTED_HUB_URL + HUB_CMDS[cmd_key] + str(light_rid)
    s = HTTPS_SESSION
    if 'get' in cmd_key:
        cmd_ptr = s.get
    elif 'set' in cmd_key:
        cmd_ptr = s.put
    header = API_HEADER.split(":")
    key_header = {header[0] : header[1]}
    setup_req = cmd_ptr(url, headers=key_header, json=payload, verify=False)
    return setup_req.json()

def get_all_hub_light_info():
    light_info_json = call_hub_api_cmd("get_lights")
    light_data = create_light_data_structs(light_info_json['data'])
    return light_data

def get_single_light_info(this_light_rid):
    data = call_hub_api_cmd('get_light_info', light_rid=this_light_rid)
    return data

def set_light_call(this_light_rid, cmd_id, values):
    cmd = HUB_LIGHT_SET_OPTIONS[cmd_id]
    try:
        payload = HUB_CMD_BODYS[cmd].format(values)
    except:
        payload = HUB_CMD_BODYS[cmd].format(*values)
    # print(payload)
    payload = json.loads(payload)
    result = call_hub_api_cmd(cmd, light_rid=this_light_rid, payload=payload)
    return result

#TODO: Finish writing out this test function that checks cmd payload formatting
def test_set_light_cmds():
    cmd = HUB_LIGHT_SET_OPTIONS[cmd_id]
    try:
        payload = HUB_CMD_BODYS[cmd].format(values)
    except:
        payload = HUB_CMD_BODYS[cmd].format(*values)
    print(payload)