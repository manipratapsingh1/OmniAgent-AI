# backend/app/knowledge/rag_system.py
"""
RAG (Retrieval Augmented Generation) System
- Reads PDFs / documents
- Provides answers based on uploaded data
"""
from typing import List, Dict, Any, Optional
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import os


class RAGSystem:
    """Retrieval Augmented Generation System"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)
        self.persist_directory = persist_directory
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    # ============= PDF PROCESSING =============
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
        return text
    
    def process_document(self, file_path: str, document_name: str) -> Dict:
        """Process PDF/document and add to vectorstore"""
        # Extract text
        if file_path.endswith('.pdf'):
            content = self.extract_text_from_pdf(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # Split into chunks
        chunks = self.text_splitter.split_text(content)
        
        # Create vectorstore if not exists
        if self.vectorstore is None:
            self.vectorstore = Chroma.from_texts(
                texts=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
                metadatas=[{"source": document_name}] * len(chunks)
            )
        else:
            self.vectorstore.add_texts(
                texts=chunks,
                metadatas=[{"source": document_name}] * len(chunks)
            )
        
        return {
            "status": "success",
            "document": document_name,
            "chunks": len(chunks),
            "tokens_approx": len(content) // 4
        }
    
    # ============= RAG QUERY =============
    def query_knowledge(self, query: str, k: int = 5) -> Dict:
        """Query knowledge base and get answer from LLM"""
        if self.vectorstore is None:
            return {"error": "No documents loaded yet"}
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": k}),
            prompt=PromptTemplate(
                template="""Use the following context to answer the question.
If you cannot find the answer in the context, say so clearly.

Context: {context}

Question: {question}

Answer:""",
                input_variables=["context", "question"]
            ),
            return_source_documents=True
        )
        
        result = qa_chain({"query": query})
        
        return {
            "answer": result["result"],
            "sources": [
                {
                    "document": doc.metadata.get("source"),
                    "content_snippet": doc.page_content[:200]
                }
                for doc in result.get("source_documents", [])
            ]
        }
    
    def get_document_summary(self, document_name: str) -> str:
        """Get summary of a document"""
        from langchain.chains.summarize import load_summarize_chain
        
        if self.vectorstore is None:
            return "No documents loaded"
        
        # Retrieve all chunks for this document
        results = self.vectorstore.similarity_search(
            document_name,
            k=100,
            filter={"source": document_name}
        )
        
        if not results:
            return "Document not found"
        
        docs = [{"page_content": r.page_content} for r in results]
        
        # Summarize
        chain = load_summarize_chain(self.llm, chain_type="map_reduce")
        return chain.run(docs)
    
    def clear_knowledge_base(self):
        """Clear all stored documents"""
        if self.vectorstore:
            self.vectorstore.delete_collection()
            self.vectorstore = None
