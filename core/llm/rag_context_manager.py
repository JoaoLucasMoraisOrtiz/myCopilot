import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class RAGContextManager:
    def __init__(self, top_k: int = 5, embedding_model: str = 'mixedbread-ai/mxbai-embed-large-v1'):
        self.top_k = top_k
        self.embedding_model = SentenceTransformer(embedding_model)

    def find_relevant_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if len(messages) <= self.top_k + 2:
            return messages

        system_prompt = None
        if messages[0]['role'] == 'system':
            system_prompt = messages.pop(0)
        latest_user_message = messages.pop(-1)
        historical_messages = messages

        historical_contents = [msg['content'] for msg in historical_messages]
        query_content = latest_user_message['content']

        historical_embeddings = self.embedding_model.encode(historical_contents)
        query_embedding = self.embedding_model.encode([query_content])

        similarities = cosine_similarity(query_embedding, historical_embeddings)[0]
        top_k_indices = np.argsort(similarities)[-self.top_k:]
        top_k_indices_sorted = sorted(top_k_indices)
        relevant_historical_messages = [historical_messages[i] for i in top_k_indices_sorted]

        new_messages = []
        if system_prompt:
            new_messages.append(system_prompt)
        new_messages.extend(relevant_historical_messages)
        new_messages.append(latest_user_message)
        return new_messages