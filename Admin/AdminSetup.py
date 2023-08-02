import os
import sys
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
from dotenv import find_dotenv, load_dotenv
import random
import inspect
from typing import List, Dict, Callable
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    HumanMessage,
    SystemMessage,
)

load_dotenv(find_dotenv())
# embeddings = OpenAIEmbeddings()
openai.api_key = os.getenv("OPENAI_API_KEY", "")

