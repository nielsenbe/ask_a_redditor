from typing import Dict, List, Optional
from models.models import (
    Document,
    DocumentChunk,
    DocumentChunkWithScore,
    DocumentMetadataFilter,
    DocumentChunkMetadata,
    Query,
    QueryResult,
    QueryWithEmbedding,
)

from external_services.openai_ds import get_embeddings
from external_services.weaviate_ds import query


def _create_document_chunk(resp) -> DocumentChunkWithScore:
    """
    Convert from the Reddit dataset format to OpenAI format.
    """
    return DocumentChunkWithScore(
        id=resp["answer_id"],
        text=f"""Question:
{resp["question"]}
Answer:
{resp["answer"]}
Answer Commentary:
{resp["answer_commentary"] if resp["answer_commentary"] != None else 'No commentary'}
        """,
        embedding=resp["_additional"]["vector"],
        score=resp["_additional"]["score"],
        answer_score=resp["score_weighted_final"],
        metadata=DocumentChunkMetadata(
            document_id=resp["question_id"],
            source=resp["question_subreddit"],
            source_id=resp["question_subreddit"],
            url=resp["answer_url"],
            created_at=resp["question_datetime"],
            author=resp["answer_author"],
        ),
    )


def _format_result(result) -> QueryResult:
    query, responses = result
    if responses == None:
        return QueryResult(query=query, results=[])
    else:
        chunks = [_create_document_chunk(r) for r in responses]
        return QueryResult(query=query, results=chunks)


def query_vector_db(queries: List[Query]) -> List[QueryResult]:
    """
    Takes in a list of queries and filters and returns a list of query results with matching document chunks and scores.
    """
    # get a list of of just the queries from the Query list
    query_texts = [query.query for query in queries]
    query_embeddings = get_embeddings(query_texts)
    #hydrate the queries with embeddings
    queries_with_embeddings = [
        QueryWithEmbedding(**query.dict(), embedding=embedding)
        for query, embedding in zip(queries, query_embeddings)
    ]

    results = query(queries_with_embeddings)

    formatted_reults = [_format_result(r) for r in results]

    return formatted_reults