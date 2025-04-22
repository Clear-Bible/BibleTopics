"""
Usage: python src/atlas.py
"""
import json
import os

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

# TODO: Switch over to the production endpoint;
# @jacobwegner has to do a bit of work for us to get there.
#
SYMPHONY_ATLAS_GRAPHQL_ENDPOINT = os.environ.get(
    "SYMPHONY_ATLAS_GRAPHQL_ENDPOINT",
    "https://bib-bd-preview-symphony-atlas.fly.dev/graphql/",
)

transport = RequestsHTTPTransport(
    url=SYMPHONY_ATLAS_GRAPHQL_ENDPOINT,
    # TODO: Enable authorization header for "closed" textual editions
    # headers={"Authorization": "Bearer <YOUR-API-KEY_HERE>"},
)
query = gql("""query PassageByReference($filters: PassageFilter) {
  passage(filters: $filters) {
    usfmRef
    ref
    textContent
  }
}""")

variables = {
    "filters": {
        "scriptureReference": {
            "usfmRef": "MAT 2:6",
            "textualEdition": "BSB",
        }
    }
}

if __name__ == "__main__":
    client = Client(transport=transport, fetch_schema_from_transport=True)
    resp = client.execute(query, variable_values=variables)
    print(json.dumps(resp, indent=2, ensure_ascii=False))
