from flask import Flask, render_template, request
from concurrent.futures import ThreadPoolExecutor, as_completed
import hub_commands
import govee_commands

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', status=None)


def _set_hub_light(rid, state):
    return {'target': 'hub', 'rid': rid, 'result': hub_commands.set_light_call(rid, 0, state)}


def _set_govee_light(mac, model, state):
    result = govee_commands.set_govee_light(mac, model, 'turn', state)
    return {'target': 'govee', 'mac': mac, 'result': result}


@app.route('/all_on', methods=['POST'])
def all_on():
    logs = []
    futures = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        # Hue / Hub lights
        try:
            hub_commands.set_api_key()
            hub_lights = hub_commands.get_all_hub_light_info()
            for rid in hub_lights.get('rids', []):
                future = executor.submit(_set_hub_light, rid, "true")
                futures.append(future)
        except Exception as e:
            logs.append({'target': 'hub', 'error': str(e)})

        # Govee lights
        try:
            res = govee_commands.get_govee_lights_info()
            govee_commands.process_device_list(res)
            for name, info in govee_commands.GOVEE_LIGHTS.items():
                mac, model = info
                future = executor.submit(_set_govee_light, mac, model, 'on')
                futures.append(future)
        except Exception as e:
            logs.append({'target': 'govee', 'error': str(e)})

        # Wait for all requests to complete and collect results
        for future in as_completed(futures):
            try:
                logs.append(future.result())
            except Exception as e:
                logs.append({'error': str(e)})

    return render_template('index.html', status=logs)


@app.route('/all_off', methods=['POST'])
def all_off():
    logs = []
    futures = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        # Hue / Hub lights
        try:
            hub_commands.set_api_key()
            hub_lights = hub_commands.get_all_hub_light_info()
            for rid in hub_lights.get('rids', []):
                future = executor.submit(_set_hub_light, rid, "false")
                futures.append(future)
        except Exception as e:
            logs.append({'target': 'hub', 'error': str(e)})

        # Govee lights
        try:
            res = govee_commands.get_govee_lights_info()
            govee_commands.process_device_list(res)
            for name, info in govee_commands.GOVEE_LIGHTS.items():
                mac, model = info
                future = executor.submit(_set_govee_light, mac, model, 'off')
                futures.append(future)
        except Exception as e:
            logs.append({'target': 'govee', 'error': str(e)})

        # Wait for all requests to complete and collect results
        for future in as_completed(futures):
            try:
                logs.append(future.result())
            except Exception as e:
                logs.append({'error': str(e)})

    return render_template('index.html', status=logs)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
