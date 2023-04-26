from pmaw import PushshiftAPI
import praw
import itertools
import csv
import re
import json
from praw.models import MoreComments
import os

CLIENT_ID = ""
CLIENT_SECRET = ""
REDDIT_UNAME = ""

URL_REGEX = r"""((?:(?:https|ftp|http)?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|org|uk)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|uk|ac)\b/?(?!@)))"""

PRAISES = [
    'THANK YOU',
    'THANKS',
    'GOOD ANSWER',
    'GREAT ANSWER',
    'CORRECT ANSWER',
    'FANTASTIC',
    'INFORMATIVE',
    'FASCINATING',
    'WELL WRITTEN'
]

def clean_text(body):
    """
    In this code we are stripping out any text after EDIT: as these are usually low quality tokens like thanking for gold or commenting on spelling mistakes, etc.
    However, this may violate Reddit's ToS which forbids changing comments outside of "display purposes".
    Considering this is for ML purposes it may not matter.
    """
    if body == None:
        return None
    
    result = re.sub(r'\]\(.*?\)',  '', body) # Get rid of URLS 
    result = re.sub(URL_REGEX, '', result) # Get rid of URLS 
    result = re.sub("\*\*|\~\~|\>\!|\!\<|\[|\]|\>", "", result) # Clean Reddit markdown
    result = re.split("edit:", result, flags=re.IGNORECASE)[0] # Get rid of Edits.  Usually bragging about Reddit gold
    result = re.split("edit :", result, flags=re.IGNORECASE)[0]
    result = result.strip('\n') # Clean up newlines
    return result


def get_citations(body):
    """
    Any link is considered a citation.
    """
    return re.findall(URL_REGEX, body)


def get_priase(replies):
    """
    Look for comments that praise the answer.  Use a simple list of keywords.  Not perfect, but surprisingly effective.
    """
    praise = 0
    for reply in replies:
        if not isinstance(reply, MoreComments) and isinstance(reply.body, str):
            result = re.split("edit:", reply.body, flags=re.IGNORECASE)[0] # Get rid of Edits.  Thanking for Reddit gold contaminates the dataset
            praise = praise + int(any([x in result.upper() for x in PRAISES]))
    return praise


def get_commentary(replies):
    """
    Pull in top comment for an answer.  We try to filter out non useful replies.
    """
    for reply in replies:
        if isinstance(reply, MoreComments) or not isinstance(reply.body, str) or reply.score < 20 or '?' in reply.body or len(reply.body) < 100:
            continue
        else:
            return clean_text(reply.body)

def process_rows(rows, reddit):
    ids = [x[0] for x in rows]
    qa_pairs = []
    for sub in reddit.info(fullnames=ids):
        if sub.score < 20 or sub.selftext == '[removed]' or sub.selftext == '[deleted]':
            continue
        question = clean_text(sub.title  + ('\n' if sub.selftext != '' else '') + sub.selftext)
        rank = 1
        sub.comment_sort = "top"
        for comment in sub.comments:
            if isinstance(comment, MoreComments) or comment.distinguished != None or comment.body == '[removed]' or comment.body == '[deleted]' or comment.score < 20 or rank > 10:
                continue
            qa = {
                'question_id': sub.fullname, 
                'question': question,
                'question_author': sub.author_fullname if sub.author != None else None,
                'question_subreddit': sub.subreddit_name_prefixed,
                'question_url': sub.shortlink,
                'question_flair': sub.link_flair_text,
                'question_marked_nsfw': sub.over_18,
                'question_datetime': sub.created_utc,
                'answer_id': comment.fullname,
                'answer': clean_text(comment.body),
                'answer_author': comment.author_fullname if comment.author != None else None,
                'answer_url':  comment.permalink,
                'answer_awards': comment.total_awards_received,
                'answer_citations': get_citations(comment.body),
                'answer_rank': rank,
                'answer_votes': comment.score,
                'answer_praises': get_priase(comment.replies),
                'answer_commentary': get_commentary(comment.replies)
            }

            rank = rank + 1
            qa_pairs.append(qa)
    return qa_pairs


def create_cleaned_files(directory, date):
    """
    1. Go through the prefiltered submissions and get the values from PRAW.
    2. Use batches of 100 for call efficiency
    3. Remove any submissions that are marked as [deleted] or [removed] or less than 20 votes (karma)
    4. Clean the Reddit markdown
    5. Gather the top 10 comments by votes
    6. Save file for further processing
    """
    file_path = os.path.join(directory, '1_CandidateSubmissions', f'RS_{date}.csv')
    output_path = os.path.join(directory, '2_CleanedDataset', f'QA_{date}.json')
    reddit = praw.Reddit(
        client_id=CLIENT_ID ,
        client_secret=CLIENT_SECRET,
        user_agent="windows:questionanswer_test:0:"+REDDIT_UNAME,
)
    with open(file_path, 'r', newline='\n', encoding="utf-8") as f:
        reader = csv.reader(f, delimiter='|')
        # Loop through the CSV file in 100-row increments
        row_count = 0
        result_count = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('[{}')
            while True:
                rows = list(itertools.islice(reader, 100))
                if not rows:
                    break
                results = process_rows(rows, reddit)
                for record in results:
                    f.write(',' + json.dumps(record))
                    f.write('\n')

                row_count = row_count + 100
                result_count = result_count + len(results)
                print('Results: ' + str(result_count))
                print('Total:   ' + str(row_count))
            f.write(']')