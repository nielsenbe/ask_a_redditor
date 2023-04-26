import pandas as pd
import glob
import openai
import os

openai.api_key = ''

median_scores = {
    'r/AskReddit': 10000,
    'r/AskMen': 800,
    'r/AskWomen': 400,
    'r/NoStupidQuestions': 100,
    'r/legaladvice': 100,
    'r/AskDocs': 100,
    'r/AskHistorians': 100,
    'r/askscience': 90,
    'r/Advice': 80,
    'r/explainlikeimfive': 80,
    'r/AskEurope': 80,
    'r/AskCulinary': 60,
    'r/AskEngineers': 60,
    'r/AskAcademia': 60,
    'r/AskAnthropology': 50,
    'r/IWantToLearn': 50,
    'r/answers': 50,
    'r/TrueAskReddit': 50,
    'r/askphilosophy':  50,
    'r/AskSocialScience':  40
    }

embedding_cache = {}


def get_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    if text in embedding_cache:
       return embedding_cache[text]
    else:
        embedding = openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']
        embedding_cache[text] = embedding
        return embedding


def normalize(col, target):
    return col.divide(target).clip(0,1)


def create_vector_files(directory, date):
    """
    1. Create quality score for the answers.
    2. Vectorize the question.
    """
    json_file = os.path.join(f"{directory}/2_CleanedDataset/QA_{date}.json")
    output_path = os.path.join(directory, '3_VectorDataset', f'VECTOR_{date}.json')

    combined_df = pd.read_json(json_file, orient="records")

    # Final cleaning
    combined_df = combined_df[combined_df['answer'].isna() == False]

    # Generate answer score
    combined_df['score_rank'] = normalize(combined_df['answer_rank'].apply(lambda val: 11-val), 10)
    combined_df['score_length'] = normalize(combined_df['answer'].apply(lambda val: len(val)), 500)
    combined_df['score_awards'] = normalize(combined_df['answer_awards'], 1)
    combined_df['score_praise'] = normalize(combined_df['answer_praises'], 1)
    combined_df['score_citations'] = normalize(combined_df['answer_citations'].apply(lambda val: len(val)), 1)
    combined_df['score_votes'] = normalize(
        combined_df['answer_votes'],
        combined_df['question_subreddit'].apply(lambda x: median_scores.get(x, 0)))
    combined_df['score_weighted_final'] = combined_df['score_rank'] * 0.15 \
        + combined_df['score_length'] * 0.25 \
        + combined_df['score_awards'] * 0.2 \
        + combined_df['score_praise'] * 0.15 \
        + combined_df['score_citations'] * 0.15 \
        + combined_df['score_votes'] * 0.1

    # Get embeddings
    combined_df['question_embedding'] = combined_df['question'].apply(lambda x: get_embedding(x, model='text-embedding-ada-002'))

    combined_df.to_json(output_path, orient="records")