
import uuid
from typing import Dict, List, Optional, Any, Tuple

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from src.rag.vector_store import LeaseVectorStore
from src.storage.lease_storage import LeaseStorage
from src.config import get_settings

class LeaseLibrarian:
    """
     Conversational AI agent for querying lease portfolio data.
     Uses RAG to answer specific questions and LeaseStorage for portfolio analytics.
    """
    
    def __init__(
        self,
        vector_store: LeaseVectorStore,
        lease_storage: LeaseStorage,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the Lease Librarian chat agent.
        
        Args:
           vector_store: Initialized vector store wrapper
           lease_storage: Initialized lease storage manager
           openai_api_key: Optional API key override
        """
        self.vector_store = vector_store
        self.lease_storage = lease_storage
        self.settings = get_settings()
        self.api_key = openai_api_key or self.settings.openai_api_key.get_secret_value()
        
        self.llm = ChatOpenAI(
            model=self.settings.openai_model, # gpt-4o-mini
            temperature=0, 
            api_key=self.api_key
        )
        
        # Store message histories by conversation_id
        self.histories: Dict[str, ChatMessageHistory] = {}
        
        # Initialize RAG chain
        self._build_chain()

    def _get_message_history(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self.histories:
            self.histories[session_id] = ChatMessageHistory()
        return self.histories[session_id]

    def _build_chain(self):
        """Build the modern LCEL RAG chain with history."""
        # 1. Retriever
        # We need the underlying FAISS vectorstore retriever
        if not self.vector_store.vector_store:
            # Fallback if index not created yet
            self.rag_chain = None
            return

        retriever = self.vector_store.vector_store.as_retriever(
            search_kwargs={"k": 4} # Retrieve top 4 relevant chunks
        )
        
        # 2. History-aware retriever prompt
        # Rephrase query based on history to make it standalone
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )
        
        # 3. Answer prompt
        system_prompt = (
            "You are the Lease Librarian, an AI assistant that helps property managers "
            "understand their lease portfolio. Answer questions accurately based on the "
            "context provided. Be concise but thorough.\n\n"
            "If the user asks about portfolio statistics (like total rent, count), "
            "use the provided PORTFOLIO STATS section.\n\n"
            "PORTFOLIO STATS:\n{portfolio_stats}\n\n"
            "CONTEXT:\n{context}"
        )
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        # 4. QA Chain
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        # 5. Full RAG Chain
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        # 6. Add message history management
        self.rag_chain = RunnableWithMessageHistory(
            rag_chain,
            self._get_message_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def get_portfolio_analytics(self) -> Dict[str, Any]:
        """Calculate high-level portfolio statistics."""
        leases = self.lease_storage.get_all_leases()
        
        total_count = len(leases)
        total_rent_monthly = sum(l.get("monthly_rent", 0) or 0 for l in leases)
        total_rent_annual = total_rent_monthly * 12
        
        lease_types = {}
        for l in leases:
            lt = l.get("lease_type") or "Unknown"
            lease_types[lt] = lease_types.get(lt, 0) + 1
            
        return {
            "total_leases": total_count,
            "total_monthly_rent": total_rent_monthly,
            "total_annual_rent": total_rent_annual,
            "lease_type_distribution": lease_types,
            "last_updated": str(datetime.now()) # for context freshness
        }

    def chat(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message and return the response.
        
        Args:
            message: User query
            conversation_id: Session ID to maintain history. Auto-generated if None.
            
        Returns:
            Dict containing answer, source_documents (ids), and conversation_id
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        # Rebuild chain if vector store wasn't ready initially
        if not self.rag_chain and self.vector_store.vector_store:
            self._build_chain()
            
        if not self.rag_chain:
            return {
                "answer": "I don't have any leases indexed yet. Please process some documents first.",
                "source_documents": [],
                "conversation_id": conversation_id
            }

        # Calculate live stats to inject into prompt
        stats = self.get_portfolio_analytics()
        stats_str = (
            f"- Total Leases: {stats['total_leases']}\n"
            f"- Total Monthly Rent: ${stats['total_monthly_rent']:,.2f}\n"
            f"- Total Annual Rent: ${stats['total_annual_rent']:,.2f}\n"
        )

        try:
            # Invoke the chain
            response = self.rag_chain.invoke(
                {"input": message, "portfolio_stats": stats_str},
                config={"configurable": {"session_id": conversation_id}}
            )
            
            # Extract source documents for citation
            # 'context' key contains list of Documents
            cites = []
            context_docs = response.get("context", [])
            seen_ids = set()
            for doc in context_docs:
                lid = doc.metadata.get("lease_id")
                if lid and lid not in seen_ids:
                    cites.append(lid)
                    seen_ids.add(lid)
            
            return {
                "answer": response["answer"],
                "source_documents": cites,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            print(f"Error in chat agent: {e}")
            return {
                "answer": f"I encountered an error processing your request: {str(e)}",
                "source_documents": [],
                "conversation_id": conversation_id
            }

from datetime import datetime
