import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError


# Function to generate documents from DataFrame rows
def generate_documents(df, index_name):
    for _, row in df.iterrows():
        yield {
            "_index": index_name,
            "_source": {
                "problem": row['problem'],
                "level": row['level'],
                "type": row['type'],
                "solution": row['solution'],
                "answer": row['answer']
            }
        }

def clean_data(df):
    # Replace NaN values with an empty string or another placeholder
    df = df.fillna('')
    df['type'] = df['type'].str.slice(0, 255)  # Truncate any long text fields
    return df

def main():
    # Load the CSV file into a DataFrame in chunks
    chunk_size = 1000  # Adjust the chunk size as needed
    chunks = pd.read_csv('./data/Qsa_train.csv', chunksize=chunk_size)

    # Initialize Elasticsearch client
    es = Elasticsearch('http://localhost:9200')

    # Define the index name
    index_name = 'math_problems'

    # Optional: Delete the index if it already exists
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)

    # Create the index (with optional custom settings and mappings)
    es.indices.create(index=index_name, body={
        "mappings": {
            "properties": {
                "question_id": {"type": "integer" },
                "problem": {"type": "text"},
                "level": {"type": "keyword"},
                "type": {"type": "keyword"},
                "solution": {"type": "text"},
                "answer": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 768  # Adjust this to match your embedding size
                }
            }
        }
    })

    # Initialize a counter for the total number of indexed documents
    total_indexed = 0

    # Process each chunk and index it
    for chunk in chunks:
        chunk = clean_data(chunk)
        try:
            bulk(es, generate_documents(chunk, index_name))
            indexed_count = len(chunk)  # Number of documents in this chunk
            total_indexed += indexed_count
            print(f"Indexed {indexed_count} documents in this chunk.")
        except BulkIndexError as e:
            print(f"Bulk index error: {e}")
            for error in e.errors:
                print(f"Failed document: {error}")

    print(f"Total documents indexed: {total_indexed}")

if __name__ == "__main__":
    main()