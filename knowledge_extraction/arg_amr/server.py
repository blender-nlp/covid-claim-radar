from flask import jsonify
from flask import Flask
from flask import request
from flask import make_response
from flask_cors import CORS
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from extract_args import extract_args

from transition_amr_parser.stack_transformer_amr_parser import AMRParser
import nltk
from nltk.tokenize import TreebankWordTokenizer

nltk.download('averaged_perceptron_tagger')
nltk.download('universal_tagset')


parser = AMRParser.from_checkpoint('./amr_model/checkpoint_best.pt')
tokenizer = TreebankWordTokenizer()
app = Flask(__name__)
CORS(app)
# request format:
# {
#   'sentences': sentences, 
#   'triggers': [[[start1, end1, trigger1, trigger_text1], [start2, end2, trigger2, trigger_text2]], [start1, end1, trigger1, trigger_text1], [start2, end2, trigger2, trigger_text2]], ...]}

@app.route('/event/detection',methods=["POST"])
def return_opinions():
    sentences = request.json["sentences"]
    triggers = request.json["triggers"]

    tokens_lists, trigs, args = extract_args(sentences, triggers, tokenizer, parser)
    results = []
    for i,arg_list in enumerate(args):
        result_dict = {"sentence": tokens_lists[i][0:-1], "events": []}
        for j,arg in enumerate(arg_list):
            event_dict = {"trigger": [trigs[i][j][0],trigs[i][j][1]], "arguments": []}
            for role in arg:
                event_dict["arguments"].append([role[0][0], role[0][1], role[1]])
            result_dict["events"].append(event_dict)
        results.append(result_dict)
    return make_response(jsonify(results), 200)

@app.route('/event/status',methods=["GET","POST"])
def return_status():
    return make_response(jsonify({'phrase' : 'Up and running'}), 200)

if __name__ == '__main__':
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(7000)
    IOLoop.instance().start()
