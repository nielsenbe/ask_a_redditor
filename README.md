# Ask a Redditor

## This repo is for reference and archival purposes.  Progress was halted on the project as Reddit's change of Terms of Services made it unviable.  The code in this repo may still be of use for personal and research purposes. 

## Overview
This research project is split into three parts:
1. QA dataset
2. ChatGPT plug-in
3. Example website

The core of this project is the QA dataset.  It is composed of 60 thousand questions and 280 thousand question/answer pairs scraped from 20 question related subreddits.

For the ChatGPT plug-in the data is loaded into a vector database [Weaviate](https://weaviate.io/).  Code is derived from the base [ChatGPT Retrieval plug-in](https://github.com/openai/chatgpt-retrieval-plugin).

The example website is a very simple HTML/Javascript wrapper around the API.

## QA Dataset
The dataset is structured in a simple way.  The title + body of the submission is the question.  The top level responses are the answers.

The data loading code is located here.  The dataset was constructed in two phases: historical and top.

The historical phase pulled submissions lists from [PushShift](https://files.pushshift.io/reddit/submissions/) going back to 2020-07. The file is decompressed and scanned to look for questions.  In this first pass the following filters are applied:
1. IS_SELF = TRUE.  In Reddit terminology a self post is simply a submission title paired with a block of text.  This type of submission is most useful for LLMs.
2. STICKIED = FALSE.  Sticked posts tend to contain meta information that isn't useful for a QA dataset.
3. Submission title ends in ? or starts with IWTL.  The goal of the dataset is to generate question / answer pairs.  IWTL is terminology from the I want to learn subreddit.  This does exclude some legitimate questions that are not formatted well.
4. Submission orginates from one of these subreddits:
* askscience
* AskHistorians
* answers
* askphilosophy
* AskEngineers
* TrueAskReddit
* AskCulinary
* NoStupidQuestions
* explainlikeimfive
* AskSocialScience
* AskDocs
* Advice
* legaladvice
* AskAnthropology
* IWantToLearn
These subreddits were selected because they focus exclusively on question answering and they maintain some level of moderation of content.

A second pass is done by querying each subreddit for the top 1000 posts.  In this pass we add the following subreddits:
* AskReddit
* AskMen
* AskWomen
* AskEurope
* AskAcademia
These subreddits were excluded from the initial pass because of lower average quality or looser rules on question/answer format.

After the initial filtering we use [PRAW](https://praw.readthedocs.io/en/stable/) to pull the live versions.
1. Exclude submissions marked as [removed] or [deleted].
2. Exclude submissions with a total vote of less than 20.  This acts as a level of quality control on the content.

We then pull in the comments (answers).
1. Exclude comments below 20 votes.
2. Only grab top 10 top level votes.
3. Exclude comments marked as [removed] or [deleted].

Per Reddit's terms of service we can only do simple modifications to the answers for purposes of display.
1. Move links out of body text.
2. Remove Reddit markdown characters.
3. Remove text after EDIT:  This is usually thanking for Reddit gold and pollutes the dataset.

We also collect the top response for each answer.  This is to provide context.
1. Apply same cleaning rules as the top level comments.
2. Exclude responses with "?".  We don't want followup questions. (Perhaps in a future version.)
3. Response character length > 100.  Want substantial commentary.

We add one additional calculationed value "answer_praises".  We scan all responses to the top level comment looking for these phrases:
* THANK YOU
* THANKS
* GOOD ANSWER
* GREAT ANSWER
* CORRECT ANSWER
* FANTASTIC
* INFORMATIVE
* FASCINATING
* WELL WRITTEN

The method is not fool proof, but is proxy way to judge the quality of an answer.

This is an example of the dataset at this stage.
```json
{
        "question_id": "t3_tzx87t",
		"question": "Why do canaries show symptoms of poisonous gas before humans do, in the context of canaries in coal mines?\nIn elementary school, I was told by the teacher that canaries have smaller lungs than humans, making them more susceptible to poisonous gas but that answer never sat well with me because smaller lungs should take in less total poison dose. Also birds are smaller than humans so the poison concentration should be fairly similar on a per weight basis. The only way I could see the bird showing symptoms first is if it has a disproportionately increased respiratory and metabolic demands compared to humans, resulting in faster accumulation of poisonous gas or that poisonous gas of equivalent dose is more potent towards canaries than to humans?",
        "question_author": "t2_t6y7f",
        "question_subreddit": "r\/askscience",
        "question_url": "https:\/\/redd.it\/tzx87t",
        "question_flair": "Biology",
        "question_marked_nsfw": 0,
		"question_datetime": 1649523094,
        "answer_id": "t1_i4288tl",
		"answer": "Canaries, like other birds, are good early detectors of carbon monoxide because they\u2019re vulnerable to airborne poisons, Inglis-Arkell\u00a0writes. Because they need such immense quantities of oxygen to enable them to fly and fly to heights that would make people altitude sick, their anatomy allows them to get a dose of oxygen when they inhale and another when they exhale, by holding air in extra sacs, he writes. Relative to mice or other easily\u00a0transportable animals that could have been carried in by the miners, they get a double dose of air and any poisons the air might contain, so miners would get an earlier warning. (Source: )",
        "answer_author": "t2_fwuhi4dc",
        "answer_url": "\/r\/askscience\/comments\/tzx87t\/why_do_canaries_show_symptoms_of_poisonous_gas\/i4288tl\/",
        "answer_awards": 0,
        "answer_citations": ["https:\/\/www.smithsonianmag.com\/smart-news\/story-real-canary-coal-mine-180961570\/"],
        "answer_rank": 1,
        "answer_votes": 833,
        "answer_praises": 1,
        "answer_commentary": "Had to learn about Chicken anatomy and how it applied to mostly all birds. Can confirm this is true. I remember it being taught that they have \"2 sets of lungs\", 1 takes most of the oxygen, as the other takes the rest as the bird exhales. Still, really informative and nice answer given.",
    }
```

At this point we prepare the data for loading into a vector database.  We calculate a quality score for the answer.

| Rule | Target | Weight | Notes |
| ---  | ---    | ---    | ---   |
| Rank      | 1                    | 0.15 | Rank 1 = 1.0 Rank 5 = .5 Rank 10 = .1 |
| Length    | 500 characters       | 0.25 | 500 characters is roughly one large paragraph.  Answe quality correlates with length. |
| Awards    | 1 Award              | 0.20 | Awards are a signal for comment quality.  Someone is willing to pay money to mark it. |
| Praise    | 1 Praise             | 0.15 | Looking for responses to answer praising it. |
| Citations | 1 URL Link           | 0.15 | Comments that provide sources or links get extra points. |
| Votes     | Varies by subreddit  | 0.10 | Votes is divided by the median vote count for that subreddit |

All sub scores are clipped to 1.0 before applying weights.  Thus a perfect final score would be 1.0

The next step is to prepare a vector the question / answer pair.  We only apply the embedding to the question portion.  This code uses the OpenAI ADA-02 model.

## ChatGPT Plug-In
Simple OpenAPI compatible plug-in built using Azure Functions.  Derived from the OpenAI example retrieval plugin.

## Web
Very simple website to test the retrieval plugin.