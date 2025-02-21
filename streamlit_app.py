import streamlit as st
import os
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



# == setup langfuse
os.environ["LANGFUSE_PUBLIC_KEY"] = st.secrets["LANGFUSE_PUBLIC_KEY"]
os.environ["LANGFUSE_SECRET_KEY"] = st.secrets["LANGFUSE_SECRET_KEY"]
langfuse = Langfuse()

st.title("All Sessions")
sessions = langfuse.fetch_sessions().data
df = pydantic_list_to_dataframe(sessions)
df
session_id = st.selectbox("Session", df['id'])
if session_id:
    st.title(session_id)
    traces = langfuse.fetch_traces(session_id=session_id)
    traces_df = pydantic_list_to_dataframe(traces.data)
    traces_df





st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
