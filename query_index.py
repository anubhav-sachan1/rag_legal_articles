import requests
import json

# Function to get embedding from OpenAI
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

def main():
    query = input("Enter your query: ")
    k = int(input("Enter the number of results you want: "))

    embedding = get_embedding(query)
    response = requests.post('http://127.0.0.1:5000/search', json={'embedding': embedding, 'k': k})

    if response.status_code == 200:
        results = response.json()
        print("Search Results:")
        for text in results['results']:
            print("##########################################################")
            print(text)
    else:
        print("Failed to query the server:", response.text)

if __name__ == "__main__":
    main()
