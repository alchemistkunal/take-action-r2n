import json
import openai
import nltk
import requests
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
import os

import transcript_manager

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'m4a', 'mp3', 'mp4', 'mpga', 'wav', 'mpeg'}
MAX_TOKENS = 2000

@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://app.takeaction.ai'
    return response

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def configure_service():
    """
    This code downloads the "punkt" package from the Natural Language Toolkit (nltk) in Python. 
    The "punkt" package provides support for tokenization, which is the process of splitting 
    a text into individual words or sentences.
    """
    nltk.download('punkt')

    # Configure the upload folder
    app.config['UPLOAD_FOLDER'] = './'


def call_whisper_api(url_audio_file, open_api_key):
    """
    Note: Currently supports only files MP3 and is locally stored
    """
    # url_audio_file = "C:\\Users\\alche\\Downloads\\(Audio) IdealFruitsTranslateOnly_2023-04-21T14_22_02.117Z.mp3"
    transcript = None
    with open(url_audio_file, "rb") as f:
        #print(open_api_key)
        openai.api_key = open_api_key
        transcript = openai.Audio.transcribe("whisper-1", f)
    # Create an empty string
    res = ''
    
    # Convert Dictionary to Concatenated String
    # Using for loop and empty string
    for item in transcript.values():
        res += str(item)
    return res


def call_openai_chat(prompt, open_api_key):
    openai.api_key = open_api_key       

    chatResponse = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",

        messages=[
            {"role": "user", "content": prompt}, 
            {"role": "system", "content": """You are an assistant that only speaks JSON. Do not write normal text.

        Example formatting:

        {
            "title": "Notion Buttons",
            "summary": "A collection of buttons for Notion",
            "action_items": [
                "item 1",
                "item 2",
                "item 3"
            ],
            "follow_up": [
                "item 1",
                "item 2",
                "item 3"
            ],
            "arguments": [
                "item 1",
                "item 2",
                "item 3"
            ],
            "related_topics": [
                "item 1",
                "item 2",
                "item 3"
            ]
            "sentiment": "positive"
        }
                    """}]
        )
    
    return chatResponse



@app.route('/upload', methods=['POST'])
def upload_file():
    print("received file")
    print(request.form)
    
    path_file = ''
    # Check if the file is present in the request
    if 'input_url' in request.form:
        # If file is not present in the request body, check for URL

        url = request.form['input_url']
        # Make a request to download the file from the URL
        try:
            response = requests.get(url)
            # TODO check of file format 
            # TODO security - malicious file 

            # Set the filename to the last part of the URL
            filename = url.split('/')[-1]
            path_file = app.config['UPLOAD_FOLDER'] + filename
            with open(path_file, 'wb') as f:
                f.write(response.content)
        except:
            return jsonify({'error': 'Unable to download file from URL.'}), 400

    else:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected.'}), 400
        if not file.filename.split('.')[-1].lower() in ['m4a', 'mp3', 'mp4', 'mpga', 'wav', 'mpeg']:
            return jsonify({'error': 'Invalid file type.'}), 400

        filename = secure_filename(file.filename)
        path_file = app.config['UPLOAD_FOLDER'] + filename

        file.save(path_file)
    response_api = ""
    response_api = run_service_logic(path_file, request)
    #with open("./response_summary.txt") as f:
    #    response_api = json.loads(f.read())
    try:
        os.remove(path_file)
    except OSError:
        pass

    return jsonify(response_api), 200

def run_service_logic(full_path_audio_file, request_data):
    open_api_key = request_data.form.get('openAI_key')
    audio_transcript = call_whisper_api(full_path_audio_file, open_api_key)
    #print("audio_transcript => " + audio_transcript + "\n\n\n")
    #audio_transcript = "Try from here. Yeah, now you try. Check, check, one, two, three, check. Stop recording."
    #with open("./transcript.txt") as f:
    #    audio_transcript = f.read()
    with open("./transcript.txt", "w") as f:
        f.write(audio_transcript)
    print("transcribed!! ")
    split_transcript = transcript_manager.split_transcript(audio_transcript, MAX_TOKENS)
    print("Transcript character length = {len}".format(len=len(audio_transcript)))
    print("Transcript word length = {len}".format(len=len(audio_transcript.split(" "))))
    print("Split of transcript into = {len}".format(len=len(split_transcript)))

    response_summary_list = []
    for part_transcript in split_transcript:
        prompt = transcript_manager.create_prompt_for_chat(part_transcript, request_data)
        print("prompt => " + prompt + "\n\n\n")
        response_summary = call_openai_chat(prompt=prompt, open_api_key=open_api_key)
        print("response =>" + json.dumps(response_summary)+ '\n\n')
        response_summary_list.append(response_summary)

    formated_document_details = transcript_manager.structure_response(response_summary_list, request_data)
    print("formated_document_details => {sum}\n\n\n".format(sum=json.dumps(formated_document_details)))
    with open("./response_summary.txt", "w") as f:
        f.write(json.dumps(formated_document_details))

    # transcript_and_summary = format_paragraphs(formated_document_details)
    return formated_document_details

@app.route('/api/health-status', methods=['GET'])
def health_check():
    return jsonify({"healthly": True, "service":"cox3-r2n"}), 200


if __name__ == '__main__':
    configure_service()

    app.run()

