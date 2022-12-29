import sys
import requests
import json
import codecs
import os
import traceback

from load import load_lstm_cnn_elmo_model, load_lstm_cnn_model, \
    load_attn_fet_model
from app import run_tagger, run_classifier
from src.util import convert_result, eng_nam_post_process, convert_bio2tab, \
    merge_bio, ltf2bio, tab2bio, bio2cfet, restore_order, get_hidden_states
from ltf2bio import ltf2bio_dir
from flask import jsonify
import argparse


def typingbio_en(bio_file, eng_fet_model, eng_fet_vocabs, output_fine_grain_model):
    try:
        bio_str = codecs.open(bio_file, encoding="utf-8").read()
        fet_json_str = bio2cfet(bio_str)
        tsv_str = run_classifier(eng_fet_model, eng_fet_vocabs, fet_json_str)
        with codecs.open(output_fine_grain_model, 'a', encoding="utf-8") as fw:
            fw.write(tsv_str)
            fw.write('\n')
    except Exception:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = 'unexpected error: %s | %s | %s' % \
              (exc_type, exc_obj, exc_tb.tb_lineno)
        print(msg)


# def typingbio_api(bio_str, lang_code):
#     try:
#         # bio_str = request.form['bio']
#         fet_json_str = bio2cfet(bio_str)
#         # lang_code = request.form['lang']
#         if lang_code == 'en':
#             tsv_str = run_classifier(eng_fet_model, eng_fet_vocabs, fet_json_str)
#             return jsonify({'tsv': tsv_str})
#         elif lang_code == 'ru':
#             tsv_str = run_classifier(rus_fet_model, rus_fet_vocabs, fet_json_str)
#             return jsonify({'tsv': tsv_str})
#         elif lang_code == 'uk':
#             tsv_str = run_classifier(ukr_fet_model, ukr_fet_vocabs, fet_json_str)
#             return jsonify({'tsv': tsv_str})
#         elif lang_code == 'es':
#             tsv_str = run_classifier(esp_fet_model, esp_fet_vocabs, fet_json_str)
#             return jsonify({'tsv': tsv_str})
#         else:
#             return jsonify({'error': 'unknown language code: {}'.format(lang_code)})
#     except Exception as e:
#         traceback.print_exc()
#         return jsonify({'error': str(e)})

if __name__ == '__main__':
    # if len(sys.argv) < 3:
    #     print(sys.argv)
    #     print('USAGE: python <lang> <cfet_json_file> <fine_grain_model output file>')
    #     exit()
    # lang = sys.argv[1]
    # # cfet_json_file = sys.argv[2]
    # bio_file = sys.argv[2]
    # fine_grain_model = sys.argv[3]
    # eval = 'm36'
    
    parser = argparse.ArgumentParser()
    # parser.add_argument('--eval', default='m36', type=str, help='eval phase 36')
    # parser.add_argument('--bio_file', default='', type=str, help='bio file')
    parser.add_argument('--ltf_input', default='', type=str, help='ltf_input')
    parser.add_argument('--output', default='', type=str, help='output dir')
    args = parser.parse_args()

    bio_file = os.path.join(os.path.dirname(args.ltf_input), 'bio.txt')
    output_fine_grain_model = args.output

    ltf2bio_dir(args.ltf_input, bio_file, ltf_filelist=None, separate_output=False)

    eval = 'm36' #args.eval
    gpu = True
    
    # model_dir = './models/'
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    elmo_option = os.path.join(model_dir, 'eng.original.5.5b.json')
    elmo_weight = os.path.join(model_dir, 'eng.original.5.5b.hdf5')
    nominal_type_dir = os.path.join(model_dir, 'nominal_text')
    # Preload models
    # eng_nam_model, eng_nam_vocabs = load_lstm_cnn_elmo_model(
    #     os.path.join(model_dir, 'eng.nam.mdl'), elmo_option, elmo_weight)
    # eng_nom_5type_model, eng_nom_5type_vocabs = load_lstm_cnn_elmo_model(
    #     os.path.join(model_dir, 'eng.nom.5type.mdl'), elmo_option, elmo_weight)
    # eng_nom_wv_model, eng_nom_wv_vocabs = load_lstm_cnn_elmo_model(
    #     os.path.join(model_dir, 'eng.nom.wv.mdl'), elmo_option, elmo_weight)
    # eng_pro_model, eng_pro_vocabs = load_lstm_cnn_elmo_model(
    #     os.path.join(model_dir, 'eng.pro.mdl'), elmo_option, elmo_weight)
    # rus_nam_5type_model, rus_nam_5type_vocabs = load_lstm_cnn_model(
    #     os.path.join(model_dir, 'rus.nam.5type.mdl'))
    # rus_nam_wv_model, rus_nam_wv_vocabs = load_lstm_cnn_model(
    #     os.path.join(model_dir, 'rus.nam.wv.mdl'))
    # ukr_nam_5type_model, ukr_nam_5type_vocabs = load_lstm_cnn_model(
    #     os.path.join(model_dir, 'ukr.nam.5type.mdl'))
    # ukr_nam_wv_model, ukr_nam_wv_vocabs = load_lstm_cnn_model(
    #     os.path.join(model_dir, 'ukr.nam.wv.mdl'))
    eng_fet_model, eng_fet_vocabs = load_attn_fet_model(
        os.path.join(model_dir, 'eng.fet.attnfet.%s.mdl' % eval), gpu=gpu)
    # rus_fet_model, rus_fet_vocabs = load_attn_fet_model(
    #     os.path.join(model_dir, 'rus.fet.attnfet.mdl'), gpu=gpu)
    # ukr_fet_model, ukr_fet_vocabs = load_attn_fet_model(
    #     os.path.join(model_dir, 'ukr.fet.attnfet.mdl'), gpu=gpu)
    # esp_fet_model, esp_fet_vocabs = load_attn_fet_model(
    #     os.path.join(model_dir, 'esp.fet.attnfet.mdl'), gpu=gpu)


    # typing(lang, cfet_json_file, fine_grain_model)
    typingbio_en(bio_file, eng_fet_model, eng_fet_vocabs, output_fine_grain_model)
