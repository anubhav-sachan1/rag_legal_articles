# AI Infrastructure Project for Harvey.

## System Requirements
- Python 3.10
- Conda environment (recommended for managing dependencies)
- Internet access for API calls and crawling tasks

## Setup Instructions
1. Unzip the zip file `code.zip`.
2. **Create the Conda environment:**
Create a Conda environment using the provided `environment.yaml` file. This environment will set up Python 3.10 and all required packages.
```
conda env create -f environment.yaml
```
3. **Activate the Conda environment:**
```
conda activate harvey_ai_infra_assignment
```

## Environment Details
The `environment.yaml` file contains all the necessary dependencies, including:
- **Flask** for web application requirements.
- **Pandas** and **BeautifulSoup4** for data manipulation and HTML parsing.
- **FAISS** for efficient similarity search of embeddings.
- **Selenium** and related tools for web scraping.
- **PyMuPDF** for PDF text extraction.
- **Spacy** and **LangChain** for text processing and chunking.

## Usage

This project is structured to run specific tasks through bash scripts that handle different components of the system. Below are the steps to execute each script:

**For convenience, the crawled files, chunks, embeddings and the FAISS index are included in `code.zip`. The user can choose to directly skip to step 5.**

### 1. Running Crawlers

Use `run_crawler.sh` to execute all crawlers defined in the configuration file. This script fetches data from various websites based on specified crawler configurations. Before running this script, please create an account on the [Linklaters website](https://www.linklaters.com/en/knowledge). The specific website requires a registered account to successfully crawl all the articles. 
```bash
./run_crawler.sh -c path/to/custom/crawler_config.json
```
The `-c` option allows you to specify a custom configuration file if needed.  

### 2. Running Chunker
After crawling, use `run_chunker.sh` to chunk the collected data into manageable pieces.
```bash
./run_chunker.sh -t 4 -c path/to/custom/chunker_config.json
```
The `-t` option allows you to set the number of threads for concurrent chunking. The `-c` option specifies a custom configuration file for the chunker.

### 3. Running Embedder
Execute `run_embedder.sh` to generate embeddings from the chunked text.
```bash
./run_embedder.sh -t 4
```
You can modify the number of threads with the `-t` option to increase or decrease parallel processing.

### 4. Running Indexer
Use `run_indexer.sh` to create a searchable index from the generated embeddings.
```bash
./run_indexer.sh
```
This script compiles embeddings into a FAISS index for efficient similarity searches.

### 5. Launching the Server
Start the server using `run_server_launcher.sh`, which hosts the API for querying the index.
```
./run_server_launcher.sh
```

### 6. Querying the Index
After the server is running, execute `run_index_querier.sh` in a **separate shell** to query the index via the launched API. This script makes an API call to GPT-4 to generate a response to the query with the results from the index.
```bash
./run_index_querier.sh
```
Note: Ensure that the server is active before running `run_index_querier.sh` as it depends on the server to process queries.

## Sample Reponse

The following shows a sample response from GPT-4 with the context obtained from the FAISS index. 

```
./run_index_querier.sh
Enter your query: Russia and Ukraine 2024
Enter the number of results you want: 10
```
**GPT-4 Response**
```
The situation between Russia and Ukraine in 2024 remains tense following Russia's invasion of Ukraine in 2022. The U.S. and EU have imposed numerous sanctions on Russia, targeting its economy and assets. In response, Russia has taken measures such as seizing U.S.-owned assets within its borders and implementing regulations that restrict multinational companies from extracting cash or selling their Russian assets. In turn, the U.S. has passed the REPO for Ukrainians Act, which provides a framework for the seizure of Russian sovereign assets and their repurposing for the support of Ukraine. However, this has not been implemented yet. Companies operating in Russia are at risk of losing control or ownership of their businesses, and there is a possibility that Russia could target industries it has previously left untouched. The situation is dynamic and companies are advised to monitor developments closely.
```

### Contact

For any queries regarding this project, please email [Anubhav](mailto:anubhav.sachan1@gmail.com).

## APPENDIX: Explanation of Workflow

### 1. Crawler

The crawler is structured to efficiently manage multiple crawler scripts tailored for different websites. Each scraper script, such as `cooley_crawler.py`, `goodwin_crawler.py`, and others, is designed to extract HTML and/or PDF files, from their respective legal firm websites. These files are then stored within a designated files subdirectory under each firm-specific folder.

The main file, `run_crawlers.py`, orchestrates the execution of these individual crawler scripts based on configurations specified in `crawler_config.json`. This setup allows for a modular approach where each crawler operates independently but is coordinated through a central script, enhancing maintainability and scalability.

The scrapers utilize a base class defined in `scraper_base.py`, which standardizes common functionalities such as initiating a web driver and handling web page interactions. This base class ensures that all scraper scripts adhere to a uniform structure, making the codebase cleaner and more consistent.

Each website-specific directory also contains a `publications.csv` file, which logs the metadata of the scraped content, including titles, URLs, and publication dates. This CSV file plays a crucial role in tracking the data extracted during the scraping process and serves as a reference for further processing or auditing tasks.

### 2. Chunker

The chunker processes and segments text extracted from various legal documents into manageable chunks. This is done using the `chunk_text.py` script, which uses the `SpacyTextSplitter` from the `langchain` library. Each document's text is first normalized and encoded to ASCII. The script breaks down the text into smaller pieces based on a predefined maximum chunk length of 4000 characters.

The `Chunker` class initializes with a configuration specifying the input directory (like `www.goodwinlaw.com`), the output directory under the chunker directory, and HTML element details used for scraping the text. It processes each file within the specified directory, extracts the text, segments it into chunks, and then saves these chunks to a `chunks.csv` file in the corresponding output directory.

This setup allows for parallel processing of multiple directories using Python’s `ThreadPoolExecutor`, which helps speed up the chunking process by handling multiple directories concurrently. The configuration for each chunker instance is specified in `chunker_config.json`.

### 3. Embedder

The embedder transforms textual chunks into numerical embeddings using OpenAI's API.

The script operates by reading chunked text data from CSV files located in the `chunker` directory. The embeddings are obtained by sending the chunked text to OpenAI's API, which returns a numerical vector representation of each text chunk.

Here's how the Embedder works:

- **Initialization**: Each instance of `EmbeddingsGenerator` is initialized with specific input and output directories, along with an API key for authentication with OpenAI's services.
- **Reading Data**: The script reads `chunks.csv` from the designated input directory, ensuring only directories containing this file are processed.
- **Batch Processing**: Text data is grouped to create batches of upto 2048 chunks for each API call.
- **API Interaction**: Text batches are sent to OpenAI’s embedding API. The script handles potential data issues like non-string types or NaN values by cleaning the batches before submission.
- **Data Storage**: The obtained embeddings are saved back to a `chunk_embeddings.csv` in the corresponding output directory under `embedder`.

This component also supports multithreading to parallelize embedding generation across multiple directories, speeding up the process when dealing with large volumes of data.

### 4. Indexer

The indexer leverages the FAISS (Facebook AI Similarity Search) library to build an efficient search index from the embeddings generated by the embedder component. It utilizes the Inverted File with Flat encoding (IVFFlat) index structure

**Key features of the IVFFlat Index:**

- **Voronoi Clustering**: The IVFFlat index uses Voronoi partitioning to divide the embedding space into distinct clusters (specified by the `nlist` parameter), allowing for faster retrieval by narrowing down the search space to relevant clusters.
- **Flat Encoding:** Inside each Voronoi cluster, IVFFlat maintains a simple flat list of vectors without any further encoding, balancing memory usage and search accuracy.
- **Quantizer:** A quantizer (IndexFlatL2) is used for assigning vectors to clusters based on the L2 distance, optimizing the indexing process for Euclidean distances which is common in embedding spaces.

The workflow is as follows:

- **Combining Data**: The indexer loads all `chunk_embeddings.csv` files from the `embedder` directory, combining them into a single DataFrame.
- **Index Creation:** Using the combined embeddings, the indexer initializes and trains the FAISS index. Post-training, the embeddings are added to the index, which is then serialized and saved to disk.
- **Text Mapping:** Alongside the index, a mapping of index positions to original text chunks is saved using Python’s pickle serialization, facilitating the retrieval of human-readable results during searches.

### 5. Server Launcher

The Server Launcher component employs Flask to expose the embedding index as a RESTful search API. 

**Workflow:**

- **Flask Setup**: Initializes a Flask application to manage incoming HTTP requests.
- **Index Loading:** Loads the FAISS index and the text mapping from serialized files. These resources are read from disk once and held in memory to facilitate quick access during search operations.
- **Search Endpoint:** Defines a `/search` endpoint that accepts POST requests containing a JSON payload with an embedding vector and an optional k value specifying the number of nearest neighbors to return. The endpoint converts these embeddings into FAISS-compatible formats, performs the search against the FAISS index, and retrieves the top k results based on distance metrics.
- **Result Formatting:** Translates indices into the corresponding text chunks using the pre-loaded mapping and packages the results and distances into a JSON response.

The Flask app is configured to run on port 5000 locally.

### 6. Index Querier

The Index Querier is used to query the Flask server set up by the Server Launcher and to leverage GPT-4 for generating context-aware answers from the results.

**Workflow**:

- **Get Embedding**: Converts user input into an embedding vector using OpenAI's `text-embedding-3-small` model.
- **Submit Query**: Sends the generated embedding to the Flask server's search endpoint, retrieves the top k results, and saves these results for further processing.
- **Interact with GPT-4:** Uses the saved search results as context to frame a question to GPT-4, and obtain an answer with the relevant context.

This component is typically run in a separate terminal or background process after the server has been initiated.
