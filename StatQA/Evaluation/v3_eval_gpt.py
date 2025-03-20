import asyncio
import aiohttp
import srsly
import http.client
import json
from tqdm import tqdm
import pandas as pd
import fire


# python -u ./Evaluation/my_eval_gpt.py \
#  --file_path="/home/yzhang6375/NL2INS/StatQA/Data/Integrated Dataset/Dataset with Prompt/Test Set/mini-StatQA for zero-shot.csv" \
#  --model_name="gpt-4o"

def main_eval(file_path, model_name = "gpt-4o",suffix = ''):
    # file_path = "/home/yzhang6375/NL2INS/StatQA/Data/Integrated Dataset/Dataset with Prompt/Test Set/mini-StatQA for zero-shot.csv"
    save_path = file_path.replace(".csv","_{}_res.json".format(model_name))
    pref = '/home/yzhang6375/NL2INS/StatQA/'
    save_path = pref+f'Model Answer/Origin Answer/{model_name}_{suffix}.csv'
    data = pd.read_csv(file_path)

    data_json_str = data.to_json(orient='records', lines=True)
    data_json = [json.loads(line) for line in data_json_str.splitlines()]

    API_KEY = 'sk-xxx'

    BASE_URL = "https://api.gpt.ge/v1/"
    # BASE_URL = "https://run.v36.cm/v1"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    async def create_completion(session, content):
        try:
            async with session.post(
                url=f"{BASE_URL}chat/completions",
                json={
                    # "model": "gpt-4o",
                    "model": model_name,
                    # "max_tokens": 30,
                    "temperature": 0.0000000000000000000,
                    "messages": [{"role": "user", "content": content['prompt']}],
                },
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    completion = result['choices'][0]['message']['content']
                    content['model_answer'] = completion
                    return completion
                else:
                    print(f"请求失败，状态码: {response.status}")
                    print(f"响应内容: {await response.text()}")
                    content['model_answer'] = ''
                    return None
        except Exception as e:
            print(f"请求发生异常: {e}")
            return None
        
    async def main():
        max_limits = 100  # parallel
        semaphore = asyncio.Semaphore(max_limits)
        results = []

        async with aiohttp.ClientSession() as session:
            tasks = []

            for content in data_json:
                task = asyncio.create_task(limited_create_completion(session, content, semaphore))
                tasks.append(task)

            for future in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
                result = await future
                results.append(result)

        return results

    async def limited_create_completion(session, content, semaphore):
        async with semaphore:
            return await create_completion(session, content)
        
    responses = asyncio.run(main())
    json_data = json.dumps(data_json)
    df = pd.read_json(json_data)
    df.to_csv(save_path, index=False)
    # srsly.write_json(save_path, data_json)
    print("####END####")


if __name__ == "__main__":
    fire.Fire(main_eval)