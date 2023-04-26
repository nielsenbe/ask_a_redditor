import weaviate
import json
import os
import pandas as pd

WEAVIATE_KEY = ''
WEAVIATE_URL = ''

SCHEMA = {
    "class": "ASKAREDDITOR",
    "description": "TEST CLASS",
    "properties": [
    {
        "name": "question_id",
        "dataType": ["string"],
        "description": "Main ID"
    },
    {
        "name": "question",
        "dataType": ["string"],
        "description": "Main ID"
    },
    {
        "name": "question_author",
        "dataType": ["string"],
        "description": "Main ID"
    },
    {
        "name": "question_subreddit",
        "dataType": ["string"],
        "description": "Main ID"
    },
    {
        "name": "question_url",
        "dataType": ["string"],
        "description": "Main ID"
    },
    {
        "name": "question_flair",
        "dataType": ["string"],
        "description": "Main ID"
    },
    {
        "name": "question_marked_nsfw",
        "dataType": ["int"],
        "description": "Main ID"
    },
    {
        "name": "question_datetime",
        "dataType": ["int"],
        "description": "Date created in UNIX format."
    },
    {
        "name": "answer_id",
        "dataType": ["string"],
        "description": "Unique ID for comment."
    },
    {
        "name": "answer",
        "dataType": ["string"],
        "description": "Main ID"
    },
    {
        "name": "answer_author",
        "dataType": ["string"],
        "description": "Main ID"
    },
    {
        "name": "answer_url",
        "dataType": ["string"],
        "description": "Main ID"
    },
    {
        "name": "answer_awards",
        "dataType": ["int"],
        "description": "Main ID",
        "indexInverted": False
    },
    {
        "name": "answer_citations",
        "dataType": ["string[]"],
        "description": "Main ID",
        "indexInverted": False
    },
    {
        "name": "answer_rank",
        "dataType": ["int"],
        "description": "Main ID",
        "indexInverted": False
    },
    {
        "name": "answer_score",
        "dataType": ["int"],
        "description": "Main ID",
        "indexInverted": False
    },
    {
        "name": "answer_praises",
        "dataType": ["int"],
        "description": "Main ID",
        "indexInverted": False
    },
    {
        "name": "answer_commentary",
        "dataType": ["string"],
        "description": "Main ID",
        "indexInverted": False
    },
    {
        "name": "score_rank",
        "dataType": ["number"],
        "description": "Scoring",
        "indexInverted": False
    },
    {
        "name": "score_length",
        "dataType": ["number"],
        "description": "Scoring",
        "indexInverted": False
    },
    {
        "name": "score_awards",
        "dataType": ["number"],
        "description": "Scoring",
        "indexInverted": False
    },
    {
        "name": "score_praise",
        "dataType": ["number"],
        "description": "Scoring",
        "indexInverted": False
    },
    {
        "name": "score_citations",
        "dataType": ["number"],
        "description": "Scoring",
        "indexInverted": False
    },
    {
        "name": "score_votes",
        "dataType": ["number"],
        "description": "Scoring",
        "indexInverted": False
    },
    {
        "name": "score_weighted_final",
        "dataType": ["number"],
        "description": "Scoring"
    }
    ]
}


def upload_to_db(directory, date):
    """
    1. Upload data to Weaviate
    """
    json_file = os.path.join(f"{directory}/3_VectorDataset/VECTOR_{date}.json")

    auth_config = weaviate.auth.AuthApiKey(api_key=WEAVIATE_KEY)
    client = weaviate.Client(WEAVIATE_URL, auth_client_secret=auth_config)

    if not client.schema.contains(SCHEMA):
        client.schema.create_class(SCHEMA)

    # Filter to only top answer per question
    df = pd.read_json(json_file, orient="records")

    grouped = df.groupby('question_id', group_keys=False)

    result = grouped.apply(lambda g: g.nlargest(1, 'score_weighted_final'))

    # Load data
    with client.batch as batch:
        batch.batch_size=100
        for _, doc_chunk in result.iterrows():
            doc_chunk = doc_chunk.to_dict()
            doc_uuid = weaviate.util.generate_uuid5(doc_chunk, SCHEMA)
            embedding = doc_chunk.pop('question_embedding')
            batch.add_data_object(
                uuid=doc_uuid,
                data_object=doc_chunk,
                class_name="ASKAREDDITOR",
                vector=embedding
                )