import logging
import requests
import yaml
import json
from hub_commands import *
from govee_commands import *

### HUE TESTING
# # logging.basicConfig(level=logging.DEBUG)
# set_api_key()
# print(USERKEY)

# ## Get lights linked to hub -- requires keys
# hub_lights = get_all_hub_light_info()
# rid = hub_lights["rids"][0]
# name = hub_lights["names"][0]
# print(name)
# print(get_single_light_info(rid))

# print(set_light_call(rid, 0, "true"))
# set_light_call(rid, 1, 50)
# print(set_light_call(rid, 2, [1, 1]))
# # light_data = create_light_data_structs(lights)
# # #TODO: break up into rooms?

### GOVEE TESTING

res = get_lights_lookup()
# print(res)