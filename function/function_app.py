import azure.functions as func
import logging
from typing import Union
import json
from services.query_service import query_vector_db
from models.api import QueryRequest, QueryResponse

app = func.FunctionApp()

@app.function_name(name="HttpTrigger")
@app.route(route="query")
def query(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        queries = QueryRequest.parse_obj(req.get_json())
        if not queries:
            raise AttributeError('Missing query body.')
    
        results = query_vector_db(queries.queries)

        return func.HttpResponse(
            json.dumps(QueryResponse(results=results).dict()),
            status_code=200,
            headers={
            "Access-Control-Allow-Origin" : "http://localhost:7071",
            "Access-Control-Allow-Credentials" : "true",
            "Access-Control-Allow-Methods" : "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers" : "Origin, Content-Type, Accept"}
        )
    
    except Exception as ex:
        print(ex)
        return func.HttpResponse(
            "Function generated an error.",
            status_code=400
        )