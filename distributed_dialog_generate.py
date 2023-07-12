import concurrent.futures
import configparser
import glob
import json
import os
import random
import re

from datasets import load_dataset
from tqdm.auto import tqdm

from utils import get_openai_response

def check_dialog_turns(text):
    if "<Round 10>" not in text:
        return False

    pattern = r"<[AB]>(.+?)\n(?:<[AB]>(.+?)\n)*"
    conversation = re.findall(pattern=pattern, string=text)
    if len(conversation) < 10:
        return False
    
    # return post_process(conversation)
    return True

def run(content):
    count = 0
    while True:
        count += 1
        response = get_openai_response(
            url,
            apikey,
            content           = content,
            temperature       = 0.1,
            _verbose          = False,
            frequency_penalty = 0.6,
            use_16k           = False,
        )
        if check_dialog_turns(response):
            break
        else:
            print(response)
            continue
    return response

config = configparser.ConfigParser()
config.read('config.ini')

url    = config.get('OPENAI', 'url')
apikey = config.get('OPENAI', 'apikey')
apikeys = config.get('OPENAI', 'apikeys')

for id in range(32, 45, 1):
    filename = f'psyqa_data_{str(id)}'

    data_path = os.path.join('psyqa', 'split', f'{filename}.json')
    result_path = os.path.join('psyqa', 'output', f'machine_{filename}.json')

    datas = load_dataset(
        'json',
        data_files = data_path,
        split      = 'train'
    )

    print(datas)

    fp = open(result_path, 'a', encoding='utf-8')
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(
                run,
                data['template']
            ) for data in datas
        ]

        with tqdm(total=len(futures)) as pbar:
            for future, data in zip(concurrent.futures.as_completed(futures), datas):
                try:
                    data['response'] = future.result()
                    fp.write(json.dumps(data, ensure_ascii=False) + '\n') 
                    pbar.update(1)
                except Exception as e:
                    print(e)
                    pbar.update(1)
