"""
Serviço RAG customizado - Implementação própria sem dependências externas pesadas.
Permite adicionar texto direto, criar chunks, gerar embeddings e fazer busca semântica.
"""
import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import re

# Dependências leves
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class RAGCustomService:
    """Serviço RAG customizado com implementação própria."""
    
    def __init__(self, rag_id: int, storage_path: str, api_key: str = None):
        self.rag_id = rag_id
        self.storage_path = storage_path
        self.api_key = api_key
        self.client = None
        self.collection = None
        
        # Criar diretório se não existir
        os.makedirs(storage_path, exist_ok=True)
        
        # Inicializar ChromaDB
        self._init_chromadb()
    
    def _init_chromadb(self):
        """Inicializa ChromaDB."""
        if not CHROMADB_AVAILABLE:
            raise ValueError("ChromaDB não está instalado. Execute: pip install chromadb")
        
        try:
            self.client = chromadb.PersistentClient(
                path=self.storage_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Criar ou obter coleção
            collection_name = f"rag_{self.rag_id}"
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"rag_id": self.rag_id}
            )
            
            logger.info(f"ChromaDB inicializado para RAG {self.rag_id}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar ChromaDB: {str(e)}")
            raise ValueError(f"Erro ao inicializar ChromaDB: {str(e)}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Gera embedding para um texto."""
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI não está instalado. Execute: pip install openai")
        
        if not self.api_key:
            raise ValueError("API key do OpenAI não fornecida")
        
        try:
            client = openai.OpenAI(api_key=self.api_key)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {str(e)}")
            raise ValueError(f"Erro ao gerar embedding: {str(e)}")
    
    def _create_chunks(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict[str, Any]]:
        """Cria chunks do texto."""
        logger.info(f"Criando chunks: tamanho={chunk_size}, overlap={chunk_overlap}")
        
        # Limpar texto
        text = re.sub(r'\s+', ' ', text.strip())
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Tentar quebrar em palavra completa
            if end < len(text):
                # Procurar último espaço antes do limite
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk = {
                    "id": f"chunk_{chunk_id}",
                    "text": chunk_text,
                    "start": start,
                    "end": end,
                    "length": len(chunk_text),
                    "created_at": datetime.now().isoformat()
                }
                chunks.append(chunk)
                chunk_id += 1
            
            # Mover para próximo chunk com overlap
            start = end - chunk_overlap if end < len(text) else end
        
        logger.info(f"Criados {len(chunks)} chunks")
        return chunks
    
    def add_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> Dict[str, Any]:
        """Adiciona texto à base de conhecimento."""
        logger.info(f"Adicionando texto ao RAG {self.rag_id}")
        
        try:
            # Criar chunks
            chunks = self._create_chunks(text, chunk_size, chunk_overlap)
            
            # Gerar embeddings e adicionar ao ChromaDB
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                # Gerar embedding
                embedding = self._generate_embedding(chunk["text"])
                
                # Preparar dados para ChromaDB
                documents.append(chunk["text"])
                embeddings.append(embedding)
                metadatas.append({
                    "chunk_id": chunk["id"],
                    "start": chunk["start"],
                    "end": chunk["end"],
                    "length": chunk["length"],
                    "created_at": chunk["created_at"]
                })
                ids.append(chunk["id"])
            
            # Adicionar ao ChromaDB
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Texto adicionado com sucesso: {len(chunks)} chunks")
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "total_chunks": self.collection.count(),
                "chunks": chunks
            }
            
        except Exception as e:
            logger.error(f"Erro ao adicionar texto: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Realiza busca semântica."""
        logger.info(f"Buscando: '{query}' (top_k={top_k})")
        
        try:
            # Gerar embedding da query
            query_embedding = self._generate_embedding(query)
            
            # Buscar no ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Formatar resultados
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # Converter distância para score de similaridade
                score = 1 - distance  # ChromaDB usa distância, queremos similaridade
                
                result = {
                    "context": doc,
                    "metadata": {
                        "chunk_id": metadata["chunk_id"],
                        "start": metadata["start"],
                        "end": metadata["end"],
                        "length": metadata["length"],
                        "created_at": metadata["created_at"],
                        "score": score
                    },
                    "score": score
                }
                formatted_results.append(result)
            
            logger.info(f"Busca retornou {len(formatted_results)} resultados")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Erro na busca: {str(e)}", exc_info=True)
            return []
    
    def get_chunks(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtém chunks armazenados."""
        logger.info(f"Obtendo chunks: limit={limit}, offset={offset}")
        
        try:
            # Buscar todos os documentos
            results = self.collection.get(
                limit=limit,
                offset=offset,
                include=["documents", "metadatas"]
            )
            
            chunks = []
            for doc, metadata in zip(results["documents"], results["metadatas"]):
                chunk = {
                    "id": metadata["chunk_id"],
                    "text": doc,
                    "start": metadata["start"],
                    "end": metadata["end"],
                    "length": metadata["length"],
                    "created_at": metadata["created_at"]
                }
                chunks.append(chunk)
            
            logger.info(f"Retornados {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Erro ao obter chunks: {str(e)}", exc_info=True)
            return []
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """Deleta um chunk específico."""
        logger.info(f"Deletando chunk: {chunk_id}")
        
        try:
            self.collection.delete(ids=[chunk_id])
            logger.info(f"Chunk {chunk_id} deletado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao deletar chunk: {str(e)}", exc_info=True)
            return False
    
    def reset(self) -> bool:
        """Reseta a base de conhecimento."""
        logger.info(f"Resetando RAG {self.rag_id}")
        
        try:
            # Deletar coleção
            self.client.delete_collection(self.collection.name)
            
            # Recriar coleção
            collection_name = f"rag_{self.rag_id}"
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"rag_id": self.rag_id}
            )
            
            logger.info("RAG resetado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao resetar RAG: {str(e)}", exc_info=True)
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas da base de conhecimento."""
        try:
            total_chunks = self.collection.count()
            
            return {
                "total_chunks": total_chunks,
                "rag_id": self.rag_id,
                "storage_path": self.storage_path,
                "collection_name": self.collection.name
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}", exc_info=True)
            return {
                "total_chunks": 0,
                "rag_id": self.rag_id,
                "storage_path": self.storage_path,
                "error": str(e)
            }
