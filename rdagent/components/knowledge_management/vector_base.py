import uuid
from pathlib import Path
from typing import List, Tuple, Union

import pandas as pd
from scipy.spatial.distance import cosine

from rdagent.core.knowledge_base import KnowledgeBase
from rdagent.log import rdagent_logger as logger
from rdagent.oai.llm_utils import APIBackend


class KnowledgeMetaData:
    def __init__(self, content: str = "", label: str = None, embedding=None, identity=None):
        self.label = label
        self.content = content
        self.id = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(self.content))) if identity is None else identity
        self.embedding = embedding
        self.trunks = []
        self.trunks_embedding = []

    def split_into_trunk(self, size: int = 1000, overlap: int = 0):
        """
        split content into trunks and create embedding by trunk
        Returns
        -------

        """

        def split_string_into_chunks(string: str, chunk_size: int):
            chunks = []
            for i in range(0, len(string), chunk_size):
                chunk = string[i : i + chunk_size]
                chunks.append(chunk)
            return chunks

        self.trunks = split_string_into_chunks(self.content, chunk_size=size)
        try:
            self.trunks_embedding = APIBackend().create_embedding(input_content=self.trunks)
        except Exception as e:
            # 如果embedding创建失败，使用零向量作为fallback
            import warnings
            import numpy as np
            warnings.warn(f"Failed to create trunk embeddings: {e}. Using zero vectors as fallback.")
            self.trunks_embedding = [np.zeros(768) for _ in self.trunks]

    def create_embedding(self):
        """
        create content's embedding
        Returns
        -------

        """
        if self.embedding is None:
            try:
                self.embedding = APIBackend().create_embedding(input_content=self.content)
            except Exception as e:
                # 如果embedding创建失败（例如API不可用），使用空向量作为fallback
                # 这样可以确保系统继续运行，只是RAG检索效果会降低
                import warnings
                warnings.warn(f"Failed to create embedding: {e}. Using empty vector as fallback.")
                import numpy as np
                self.embedding = np.zeros(768)  # 使用768维的零向量作为fallback

    def from_dict(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)
        return self

    def __repr__(self):
        return f"Document(id={self.id}, label={self.label}, data={self.content})"


Document = KnowledgeMetaData


def contents_to_documents(contents: List[str], label: str = None) -> List[Document]:
    # openai create embedding API input's max length is 16
    size = 16
    embedding = []
    for i in range(0, len(contents), size):
        try:
            emb = APIBackend().create_embedding(input_content=contents[i : i + size])
            embedding.extend(emb)
        except Exception as e:
            # 如果embedding创建失败，使用零向量作为fallback
            import warnings
            import numpy as np
            warnings.warn(f"Failed to create embedding for batch {i}: {e}. Using zero vectors as fallback.")
            batch_size = min(size, len(contents) - i)
            embedding.extend([np.zeros(768) for _ in range(batch_size)])
    docs = [Document(content=c, label=label, embedding=e) for c, e in zip(contents, embedding)]
    return docs


class VectorBase(KnowledgeBase):
    """
    This class is used for handling vector storage and query
    """

    def add(self, document: Union[Document, List[Document]]):
        """
        add new node to vector_df
        Parameters
        ----------
        document

        Returns
        -------

        """
        pass

    def search(self, content: str, topk_k: int | None = None, similarity_threshold: float = 0) -> List[Document]:
        """
        search vector_df by node
        Parameters
        ----------
        similarity_threshold
        content
        topk_k: return topk_k nearest vector_df

        Returns
        -------

        """
        pass


class PDVectorBase(VectorBase):
    """
    Implement of VectorBase using Pandas
    """

    def __init__(self, path: Union[str, Path] = None):
        self.vector_df = pd.DataFrame(columns=["id", "label", "content", "embedding"])
        super().__init__(path)

    def shape(self):
        return self.vector_df.shape

    def add(self, document: Union[Document, List[Document]]):
        """
        add new node to vector_df
        Parameters
        ----------
        document

        Returns
        -------

        """
        if isinstance(document, Document):
            if document.embedding is None:
                document.create_embedding()
            docs = [
                {
                    "id": document.id,
                    "label": document.label,
                    "content": document.content,
                    "trunk": document.content,
                    "embedding": document.embedding,
                }
            ]
            docs.extend(
                [
                    {
                        "id": document.id,
                        "label": document.label,
                        "content": document.content,
                        "trunk": trunk,
                        "embedding": embedding,
                    }
                    for trunk, embedding in zip(document.trunks, document.trunks_embedding)
                ]
            )
            self.vector_df = pd.concat([self.vector_df, pd.DataFrame(docs)], ignore_index=True)
        else:
            for doc in document:
                self.add(document=doc)

    def search(
        self,
        content: str,
        topk_k: int | None = None,
        similarity_threshold: float = 0,
        constraint_labels: list[str] | None = None,
    ) -> Tuple[List[Document], List]:
        """
        Search vector by node's embedding.

        Parameters
        ----------
        content : str
            The content to search for.
        topk_k : int, optional
            The number of nearest vectors to return.
        similarity_threshold : float, optional
            The minimum similarity score for a vector to be considered.
        constraint_labels : List[str], optional
            If provided, only nodes with matching labels will be considered.

        Returns
        -------
        Tuple[List[Document], List]
            A list of `topk_k` nodes that are semantically similar to the input node, sorted by similarity score.
            All nodes shall meet the `similarity_threshold` and `constraint_labels` criteria.
        """
        if not self.vector_df.shape[0]:
            return [], []

        document = Document(content=content)
        document.create_embedding()

        filtered_df = self.vector_df
        if constraint_labels is not None:
            filtered_df = self.vector_df[self.vector_df["label"].isin(constraint_labels)]

        similarities = filtered_df["embedding"].apply(
            lambda x: 1 - cosine(x, document.embedding)
        )  # cosine is cosine distance, 1-similarity

        searched_similarities = similarities[similarities > similarity_threshold]
        if topk_k is not None:
            searched_similarities = searched_similarities.nlargest(topk_k)
        most_similar_docs = filtered_df.loc[searched_similarities.index]

        docs = []
        for _, similar_docs in most_similar_docs.iterrows():
            docs.append(Document().from_dict(similar_docs.to_dict()))

        return docs, searched_similarities.to_list()
