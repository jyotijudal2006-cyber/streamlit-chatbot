import json
import time
from pathlib import Path
from typing import Dict, List, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from fastapi import HTTPException
from app.core.config import ROOT_DIR, settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

STORAGE_DIR = ROOT_DIR / "backend_storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class RAGService:
    def __init__(self):
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            self.llm = ChatGroq(
                model="llama-3.1-8b-instant",
                temperature=0,
                api_key=settings.GROQ_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize Groq components: {e}")
            self.embeddings = None
            self.llm = None

        self.vector_stores: Dict[str, FAISS] = {}
        self.session_metadata: Dict[str, Dict[str, Any]] = {}

        self.system_prompt = (
            "You are an AI assistant designed to answer questions strictly based on the provided document context. "
            "If the information required to answer the question is not present in the context, you must output exactly: "
            "'The uploaded document does not contain information about this.' "
            "Do not use external knowledge or hallucinate. Keep your answers concise and accurate.\n\n"
            "Context: {context}"
        )

    def _session_dir(self, session_id: str) -> Path:
        session_dir = STORAGE_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def _metadata_path(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "metadata.json"

    def _index_path(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "faiss_index"

    def _load_metadata(self, session_id: str) -> Dict[str, Any]:
        if session_id in self.session_metadata:
            return self.session_metadata[session_id]

        metadata_path = self._metadata_path(session_id)
        if metadata_path.exists():
            with metadata_path.open("r", encoding="utf-8") as f:
                metadata = json.load(f)
        else:
            metadata = {"file_hashes": []}
        self.session_metadata[session_id] = metadata
        return metadata

    def _save_metadata(self, session_id: str) -> None:
        metadata_path = self._metadata_path(session_id)
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(self.session_metadata[session_id], f)

    def _load_store(self, session_id: str) -> None:
        if session_id in self.vector_stores:
            return

        index_dir = self._index_path(session_id)
        if index_dir.exists():
            self.vector_stores[session_id] = FAISS.load_local(str(index_dir), self.embeddings)
            logger.info(f"Loaded existing FAISS store for session {session_id}")

    def _ensure_session(self, session_id: str) -> None:
        self._load_metadata(session_id)
        self._load_store(session_id)

    def is_configured(self) -> bool:
        return self.embeddings is not None and self.llm is not None

    def _batch_embed_documents(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        vectors: List[List[float]] = []
        for start in range(0, len(texts), batch_size):
            batch_texts = texts[start:start + batch_size]
            batch_vectors = self.embeddings.embed_documents(batch_texts)
            vectors.extend(batch_vectors)
            logger.info(f"Embedded batch {start // batch_size + 1} / {((len(texts) - 1) // batch_size) + 1}")
        return vectors

    def store_documents(self, session_id: str, chunks: list, file_hash: str) -> bool:
        if not self.is_configured():
            raise HTTPException(status_code=500, detail="Groq API is not properly configured.")

        self._ensure_session(session_id)
        metadata = self._load_metadata(session_id)

        if file_hash in metadata["file_hashes"]:
            logger.info(f"Skipping already processed file hash {file_hash} for session {session_id}")
            return False

        try:
            texts = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]

            start = time.perf_counter()
            vectors = self._batch_embed_documents(texts)
            if session_id in self.vector_stores:
                self.vector_stores[session_id].add_texts(texts, metadatas=metadatas)
            else:
                self.vector_stores[session_id] = FAISS.from_embeddings(
                    text_embeddings=zip(texts, vectors),
                    embedding=self.embeddings,
                    metadatas=metadatas,
                )
            embed_time = time.perf_counter() - start

            self.session_metadata[session_id]["file_hashes"].append(file_hash)
            self._save_metadata(session_id)
            self._save_store(session_id)

            logger.info(
                f"Stored {len(chunks)} chunks for session {session_id} in {embed_time:.2f}s. Total files: {len(self.session_metadata[session_id]['file_hashes'])}"
            )
            return True
        except Exception as e:
            logger.error(f"Error storing documents for session {session_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to process and store document embeddings.")

    def _save_store(self, session_id: str) -> None:
        index_dir = self._index_path(session_id)
        index_dir.mkdir(parents=True, exist_ok=True)
        self.vector_stores[session_id].save_local(str(index_dir))

    def query(self, session_id: str, question: str) -> str:
        if not self.is_configured():
            raise HTTPException(status_code=500, detail="Groq API is not properly configured.")

        self._ensure_session(session_id)
        if session_id not in self.vector_stores:
            raise HTTPException(status_code=400, detail="No documents uploaded for this session.")

        try:
            vector_store = self.vector_stores[session_id]
            retriever = vector_store.as_retriever(search_kwargs={"k": 4})

            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", "{input}"),
            ])

            question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
            rag_chain = create_retrieval_chain(retriever, question_answer_chain)

            response = rag_chain.invoke({"input": question})
            return response["answer"]
        except Exception as e:
            logger.error(f"Error during query for session {session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

rag_service = RAGService()
