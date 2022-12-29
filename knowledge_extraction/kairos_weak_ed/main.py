from event_detector import EventDetector
from detect import detect
from convert_outputs import convert
from flask import Flask, request, jsonify, make_response
import argparse

app = Flask(__name__)

RESOURCE_DIR = "./resources/models/covid"
ed = None

@app.route('/detect', methods=["POST"])
def run_detect():
    form = request.json
    for i in ['results']:
        try:
            assert i in form
        except AssertionError:
            return 'ERROR: Missing argument: %s' % i
    results = form['results']
    sentences, triggers = detect(detector=ed, results=results)
    return make_response(jsonify({"sentences":sentences, "triggers": triggers}), 200)


@app.route('/merge', methods=["POST"])
def merge():
    form = request.json
    for i in ['results', 'tokens', 'events']:
        try:
            assert i in form
        except AssertionError:
            return 'ERROR: Missing argument: %s' % i
    results = convert(results=form['results'], token_data=form['tokens'], event_data=form['events'])
    return make_response(jsonify(results), 200)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, default=8000)
    parser.add_argument("--resource-dir", "-r", type=str, default=RESOURCE_DIR)
    args= parser.parse_args()
    ed = EventDetector(args.resource_dir)
    app.run('0.0.0.0', port=args.port, threaded=True)







