import requests
import json

def get_embedding(text):
    with open('secret_key.txt','r') as f:
        API_KEY = f.readline().strip()
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'input': text,
        'model': 'text-embedding-3-small'
    }
    response = requests.post('https://api.openai.com/v1/embeddings', headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    else:
        raise Exception(f"Failed to get embedding: {response.text}")

def submit_query_to_gpt4(context_file, question):
    with open('secret_key.txt', 'r') as f:
        API_KEY = f.readline().strip()
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    with open(context_file, 'r') as f:
        results = json.load(f)
    
    context_messages = []
    if 'results' in results:
        for result in results['results']:
            context_messages.append({"role": "system", "content": result})
    
    context_messages.append({"role": "user", "content": question})

    data = {
        'model': 'gpt-4',
        'messages': context_messages,
        'temperature': 0.5
    }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        raise Exception(f"Failed to interact with GPT-4: {response.text}")


def main():
    query = input("Enter your query: ")
    k = int(input("Enter the number of results you want: "))
    embedding = get_embedding(query)
    response = requests.post('http://127.0.0.1:5000/search', json={'embedding': embedding, 'k': k})

    if response.status_code == 200:
        results = response.json()
        with open('index_querier/results.json', 'w') as f:
            json.dump(results, f, indent=4)

        framed_question = f"Use the above information to answer the query: '{query}'?"
        answer = submit_query_to_gpt4('index_querier/results.json', framed_question)
        print("GPT-4 Response:")
        print(answer)
    else:
        print("Failed to query the server:", response.text)

if __name__ == "__main__":
    main()
