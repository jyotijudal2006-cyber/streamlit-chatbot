import hashlib
from pathlib import Path
import os
import tempfile
from time import perf_counter
from fastapi import UploadFile, HTTPException
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import ROOT_DIR, settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

UPLOAD_DIR = ROOT_DIR / "backend_storage" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )

    def validate_file(self, file: UploadFile, content: bytes) -> None:
        """Validates file extension and size."""
        allowed_extensions = {".pdf", ".docx", ".txt"}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: pdf, docx, txt.")

        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(status_code=400, detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB.")

    async def save_upload(self, file: UploadFile) -> tuple[Path, str, str]:
        """Reads file bytes, validates, hashes, and saves a temp copy."""
        content = await file.read()
        self.validate_file(file, content)

        ext = os.path.splitext(file.filename)[1].lower()
        file_hash = hashlib.sha256(content).hexdigest()
        dest_path = UPLOAD_DIR / f"{file_hash}{ext}"

        if not dest_path.exists():
            dest_path.write_bytes(content)
            logger.info(f"Saved uploaded file {file.filename} as {dest_path}")
        else:
            logger.info(f"File {file.filename} already exists as {dest_path}, skipping re-save.")

        return dest_path, file_hash, ext

    async def extract_chunks(self, file_path: Path, ext: str) -> list:
        """Load document and split into chunks with timing logs."""
        start = perf_counter()
        docs = self._load_document(file_path, ext)
        read_time = perf_counter() - start
        logger.info(f"Read document {file_path.name} in {read_time:.2f}s")

        start = perf_counter()
        chunks = self.text_splitter.split_documents(docs)
        split_time = perf_counter() - start
        logger.info(f"Split document {file_path.name} into {len(chunks)} chunks in {split_time:.2f}s")

        return chunks

    def _load_document(self, file_path: Path, ext: str) -> list:
        if ext == ".pdf":
            loader = PyPDFLoader(str(file_path))
        elif ext == ".docx":
            loader = Docx2txtLoader(str(file_path))
        elif ext == ".txt":
            loader = TextLoader(str(file_path), encoding='utf-8')
        else:
            raise ValueError("Unsupported extension")

        return loader.load()


document_processor = DocumentProcessor()
