import pytest
import azure.functions as func
import json
from function_app import query

@pytest.mark.parametrize(
    "queries, expected_num_results",
    [
        #({"query": "Is it true that most Koreans before the war supported the North", "top_k": 3}, 3),
        #({"query": "What was considered a big town by the Romans?", "filter": {"question_subreddit": "r/AskHistorians"}}, 2),
        (
            {
                "query": "What was considered a big town by the Romans?"
            },
            1,
        )
    ],
)
def test_query(queries, expected_num_results):
    formatted_queries = {"queries": [queries]}

    json_string = json.dumps(formatted_queries)

    req = func.HttpRequest(method='POST',
                           body=json_string.encode('utf-8'),
                           url='/api/query')

    func_call = query.build().get_user_function()
    resp = func_call(req)

    assert(len(resp.results[0].results) == expected_num_results)

    print('Done')