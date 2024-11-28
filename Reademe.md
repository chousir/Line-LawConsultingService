# Based on Claude 3.5 Sonnet and RAG, LINE Law Consulting Service

## Setting Up the Environment
First, we need to install the necessary libraries. Uncomment the following line and run it to install the required packages. If the libraries are installed on your system, you can skip this step.

```bash
pip install langchain sentence-transformers anthropic langchain_community langchain_huggingface wikipedia clickhouse_connect flask line-bot-sdk
```

## Setting Up Environment Variables
Next, we need to set up the environment variables for MyScale and Claude 3 API connections. We will use MyScaleDB as a vector database for this RAG application because it offers high performance, scalability, and efficient data retrieval capabilities.
 - MyScaleDB
`https://myscale.com/`
 - Claude 3 API connections
`https://console.anthropic.com/settings/keys`


## Download verdict data 1996-2001
`https://opendata.judicial.gov.tw/`
```bash
python verdict_data_download.py
```

## unrar
```bash
for file in *.rar; do
    unrar x "$file"
done
```

## Data loading, splitting, embedding and importing data to MyScale vector store
```bash
python myscale_vector_database.py
```

## Check MyScale vector store
```sql
SELECT *
FROM wikipedia LIMIT 10;

SELECT COUNT(*) FROM wikipedia;

SELECT *
FROM verdict
WHERE text LIKE '%判決內容詳如附件。%';

SELECT *
FROM verdict
WHERE length(text) < 100;
```

## Ngrok and Line
Create the LINE Official Account "Law Consulting".
Use Ngrok to expose the local server (Flask), allowing third parties (LINE) or external systems to test and access, enabling direct access to your application.
Connect to MyScale and use similarity_search to find documents similar to the Query.
`https://dashboard.ngrok.com/get-started/your-authtoken`
 - Install ngrok via Apt with the following command:
    ```bash
    curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
        | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
        && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
        | sudo tee /etc/apt/sources.list.d/ngrok.list \
        && sudo apt update \
        && sudo apt install ngrok
    ```
 - Run the following command to add your authtoken to the default ngrok.yml configuration file.
    ```bash
    ngrok config add-authtoken {TOKEN}
    ```

## Start with Ngrok
```
python claude_rag_linebot.py
```

## Ngrok interact with Line
 - Run ngrok
    ```
    ngrok http 5000
    ```
 - extract https://5771-1-200-73-183.ngrok-free.app and input it to https://developers.line.biz/console/channel/2006544458/messaging-api Webhook URL
    `
    Session Status                online                                                                                                                     
    Account                       coolboy850319@gmail.com (Plan: Free)                                                                                       
    Version                       3.18.3                                                                                                                     
    Region                        Japan (jp)                                                                                                                 
    Latency                       64ms                                                                                                                       
    Web Interface                 http://127.0.0.1:4040                                                                                                      
    Forwarding                    https://5771-1-200-73-183.ngrok-free.app -> http://localhost:5000
    `
