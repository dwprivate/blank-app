import streamlit as st
import os
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from langfuse import Langfuse
def pydantic_list_to_dataframe(pydantic_list):
    """
    Convert a list of pydantic objects to a pandas dataframe.
    """
    data = []
    for item in pydantic_list:
        data.append(item.dict())
    return pd.DataFrame(data)

def get_scores(scores):
    base_url = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    headers = {"Content-Type": "application/json"}

    # Effectuez la requête GET pour récupérer les scores
    scoreIds = ",".join(scores)
    response = requests.get(
        f"{base_url}/api/public/scores",
        headers=headers,
        params={"scoreIds": scoreIds},
        auth=HTTPBasicAuth(
            os.getenv("LANGFUSE_PUBLIC_KEY"), os.getenv("LANGFUSE_SECRET_KEY")
        ),
    )

    # Vérifiez la réponse
    if response.status_code == 200:
        scores = response.json()
        return scores
    else:
        print(f"Erreur lors de la récupération des scores: {response.status_code}")
        print(response.text)
        return None


def get_latency_for(trace_id, name):

    data = langfuse.fetch_observations(trace_id=trace_id, name=name)
    return data.data[0].latency



# == setup langfuse
os.environ["LANGFUSE_PUBLIC_KEY"] = st.secrets["LANGFUSE_PUBLIC_KEY"]
os.environ["LANGFUSE_SECRET_KEY"] = st.secrets["LANGFUSE_SECRET_KEY"]
langfuse = Langfuse()

st.title("Prompto - Sessions Analysis")
sessions = langfuse.fetch_sessions().data
df = pydantic_list_to_dataframe(sessions)
# df
session_id = st.selectbox("Session", df['id'])
if session_id:
    st.title(session_id)
    traces = langfuse.fetch_traces(session_id=session_id)
    traces_df = pd.DataFrame(
        [
            {
                "id": trace.id,
                "question": trace.input["kwargs"]["user_message"],
                "response": trace.output,
                "latency": trace.latency,
                "total_cost": trace.total_cost,
                "scores": get_scores(trace.scores),
                "get_chunks_latency": get_latency_for(trace.id, "get_chunks"),
                "error": "ERROR" in trace.tags,
                "total_duration": trace.metadata.get("total_duration","")
            }
            for trace in traces.data
        ]
    )
    for name in ["context_relevance", "conformity", "expert_vs_ia", 'toxicity', 'response_found']:
        traces_df[name] = traces_df["scores"].apply(
            lambda scores: next(
            (
                score["stringValue"] if score.get("stringValue") is not None else score["value"]
                for score in scores["data"] if score["name"] == name
            ),
            None,
            )
        )    
    del traces_df["scores"]
    traces_df
    results = {
        "sessions_id": session_id,
        "error_percentage": 0, #TODO
        "not_found_percentage": (traces_df['response_found'] == 'NOT_FOUND').mean(),
        "found_percentage": (traces_df['response_found'] == 'FOUND').mean(),
        "total_cost_mean": traces_df["total_cost"].mean(),
        "total_latency_mean": traces_df["latency"].mean(),
        "get_chunks_latency": traces_df["get_chunks_latency"].mean()/1000,
        "context_relevance_mean": traces_df["context_relevance"].mean(),
        "expert_vs_ia": traces_df["expert_vs_ia"].mean(),
        "conformity": traces_df["conformity"].mean()
    }
    results




