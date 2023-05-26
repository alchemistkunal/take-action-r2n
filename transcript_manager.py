import re
import json
from nltk.tokenize import sent_tokenize

# Split the transcript into shorter strings if needed, based on GPT token limit
def split_transcript(transcript, max_tokens):
    strings_array = []
    current_index = 0

    while current_index < len(transcript):
        end_index = min(current_index + max_tokens, len(transcript))

        # Find the next period
        while end_index < len(transcript) and [transcript[end_index]] != ".":
            end_index += 1

        # Include the period in the current string
        if end_index < len(transcript):
            end_index += 1

        # Add the current chunk to the stringsArray
        chunk = transcript[current_index:end_index]
        strings_array.append(chunk)

        current_index = end_index

    return strings_array

def create_prompt_for_chat(transcript, request_data):
    request_prompt = 'Analyze the transcript provided below, then provide the following\n'

    if request_data.form.get('title')=='true':
        request_prompt += 'Key "title:" - add a title.\n'
    if request_data.form.get('summary') =='true':
        request_prompt += 'Key "summary" - create a summary.\n'
    if request_data.form.get('main_points') =='true': 
        request_prompt += 'Key "main_points" - add an array of the main points. Limit each item to 75 words and be concise.\n'
    if request_data.form.get('action_items') =='true':  
        request_prompt += 'Key "action_items:" - add an array of action items. Limit each item to 75 words and be concise.\n'
    if request_data.form.get('follow_up') =='true': 
        request_prompt += 'Key "follow_up:" - add an array of follow-up questions. Limit each item to 75 words and be concise.\n'
    if request_data.form.get('arguments') =='true':
        request_prompt += 'Key "arguments:" - add an array of potential arguments against the transcript. Limit each item to 75 words and be concise.\n'
    if request_data.form.get('related_topics') =='true':
        request_prompt += 'Key "related_topics:" - add an array of topics related to the transcript. Limit each item to 75 words, and limit the list to 5 items. Use sentence case.\n'
    if request_data.form.get('sentiment') =='true':
        request_prompt += 'Key "sentiment" - add an array of sentiment analysis. Use sentence case.\n'
    #if request_data.form.get('custom_prompt') is not None and request_data.form.get('custom_prompt') != '':  
    #    request_prompt += "Be creative. Try returning the response with " + request_data.form.get('custom_prompt') + '\n'
    return  request_prompt+"""
    
    Ensure that the final element of any array within the JSON object is not followed by a comma.

    Transcript:
            
            {arr}
    """.format(arr=transcript)

def structure_response(chatResponses: list, request_data) -> str:
    """
    Expects array type argument
    """
    results_array = []
    for result in chatResponses:
        # ChatGPT loves to occasionally throw commas after the final element in arrays, so let's remove them
        def remove_trailing_commas(json_string):
            regex = r",\s*(?=])"
            return re.sub(regex, "", json_string)

        # Need some code that will ensure we only get the JSON portion of the response
        # This should be the entire response already, but we can't always trust GPT
        json_string = result["choices"][0]["message"]["content"]
        json_string = re.sub(r"^[^{]*?{", "{", json_string)
        json_string = re.sub(r"}[^}]*?$", "}", json_string)
        cleaned_json_string = remove_trailing_commas(json_string)

        try:
            json_obj = json.loads(cleaned_json_string)
        except json.JSONDecodeError as error:
            print("Error while parsing cleaned JSON string:")
            print(error)
            print("Original JSON string:", json_string)
            print("Cleaned JSON string:", cleaned_json_string)
            json_obj = {}

        response = {
            "choice": json_obj,
            "usage": 0 if not result["usage"]["total_tokens"] else result["usage"]["total_tokens"],
        }

        results_array.append(response)

    chat_response = {
        # "title": results_array[0]["choice"]["title"],
        # "sentiment":  [],
        # "summary": [],
        # "main_points": [],
        # "action_items": [],
        # "arguments": [],
        # "follow_up": [],
        # "related_topics": [],
        "tokens_array": [],
    }
    
    settings = ['main_points', 'action_items', 'follow_up', 'arguments', 'related_topics', 'sentiment']
       
    for arr in results_array:
        if request_data.form.get('title') =='true':
            chat_response["title"] = (chat_response["title"] if "title" in chat_response else '') + arr['choice']['title']  
        if request_data.form.get('summary') =='true':
            chat_response["summary"] = (chat_response["summary"] if "summary" in chat_response else '') + arr['choice']['summary']  

        chat_response["tokens_array"] = (chat_response["tokens_array"] if "tokens_array" in chat_response else list())
        chat_response["tokens_array"].append(arr['usage'])
        for key in settings:
            if request_data.form.get(key) =='true':    
                chat_response[key] = (chat_response[key] if key in chat_response else list())
                chat_response[key].append(arr['choice'][key])   

    print(json.dumps(chat_response))

    def array_sum(arr):
        return sum(arr)

    final_chat_response = {
        # "1title": chat_response["title"],
        # "2summary": " ".join(chat_response["summary"]),
        # "3sentiment": [item for sublist in chat_response["sentiment"] for item in sublist],
        # "4main_points": [item for sublist in chat_response["main_points"] for item in sublist],
        # "5action_items": [item for sublist in chat_response["action_items"] for item in sublist],
        # "6arguments": [item for sublist in chat_response["arguments"] for item in sublist],
        # "7follow_up": [item for sublist in chat_response["follow_up"] for item in sublist],
        # "8related_topics": sorted(list(set([item.lower() for sublist in chat_response["related_topics"] for item in sublist]))),
        # "9tokens": array_sum(chat_response["usage_array"]),
    }

    priorityIndex = 1
    if request_data.form.get('title') =='true':
        final_chat_response[str(priorityIndex)+"title"] = chat_response["title"] 
        priorityIndex+=1
    if request_data.form.get('summary') =='true':
        final_chat_response[str(priorityIndex)+"summary"] = chat_response["summary"]
        priorityIndex+=1
    if request_data.form.get('main_points') =='true': 
        final_chat_response[str(priorityIndex)+"main_points"] = [sublist for sublist in chat_response["main_points"]],
        priorityIndex+=1
    if request_data.form.get('action_items') =='true':  
        final_chat_response[str(priorityIndex)+"action_items"] = [sublist for sublist in chat_response["action_items"]]
        priorityIndex+=1 
    if request_data.form.get('follow_up') =='true': 
        final_chat_response[str(priorityIndex)+"follow_up"] = [sublist for sublist in chat_response["follow_up"]] 
        priorityIndex+=1
    if request_data.form.get('arguments') =='true':
        final_chat_response[str(priorityIndex)+"arguments"] = [sublist for sublist in chat_response["arguments"]]   
        priorityIndex+=1
    if request_data.form.get('related_topics') =='true':
        final_chat_response[str(priorityIndex)+"related_topics"] =  sorted(list(set([item.lower() for sublist in chat_response["related_topics"] for item in sublist])))
        priorityIndex+=1
    if request_data.form.get('sentiment') =='true':
        final_chat_response[str(priorityIndex)+"sentiment"] = [sublist for sublist in chat_response["sentiment"]]
        priorityIndex+=1
    final_chat_response[str(priorityIndex)+"tokens"]= array_sum(chat_response["tokens_array"])

     

    return final_chat_response

def format_paragraphs(final_chat_response):
    transcript = final_chat_response["transcript"]
    summary = final_chat_response["summary"]
    
    transcript_sentences = sent_tokenize(transcript)
    summary_sentences = sent_tokenize(summary)
    
    def group_sentences(arr, num_sentences):
        groups = []
        
        for i in range(0, len(arr), num_sentences):
            group = []
            for j in range(i, i + num_sentences):
                if j < len(arr):
                    group.append(arr[j])
            groups.append(' '.join(group))
            
        return groups
    
    def check_char_limit(arr, limit):
        checked_arr = []
        for sentence in arr:
            if len(sentence) > limit:
                pieces = [sentence[i:i+limit] for i in range(0, len(sentence), limit) if i+limit <= len(sentence)]
                if len(''.join(pieces)) < len(sentence):
                    pieces.append(sentence[len(''.join(pieces)):])
                checked_arr.extend(pieces)
            else:
                checked_arr.append(sentence)
        return checked_arr
    
    transcript_paragraphs = group_sentences(transcript_sentences, 3)
    checked_transcript_paragraphs = check_char_limit(transcript_paragraphs, 800)
    
    summary_paragraphs = group_sentences(summary_sentences, 3)
    checked_summary_paragraphs = check_char_limit(summary_paragraphs, 800)
    
    all_paragraphs = {
        "transcript": checked_transcript_paragraphs,
        "summary": checked_summary_paragraphs
    }
    
    return all_paragraphs



def main():
    with open("./transcript.txt") as f:
        audio_transcript = f.read()

    strings_array = split_transcript(audio_transcript,2000)
    print(strings_array)
    


if __name__ == '__main__':
    main()

