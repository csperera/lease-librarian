"""
Lease Digitizer - Conflict Detector Agent

An agent with memory that identifies contradictions and conflicts between
lease documents. This agent maintains context across multiple documents
to detect inconsistencies between base leases and their amendments.

Key Features:
- Persistent memory across document analysis
- Multi-document conflict detection
- Severity classification for conflicts
- Suggested resolutions for detected issues
- Comprehensive conflict reporting
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI

from src.config import get_settings
from src.schemas.amendment import Amendment
from src.schemas.conflict import (
    Conflict,
    ConflictCategory,
    ConflictEvidence,
    ConflictReport,
    ConflictSeverity,
    DocumentReference,
    SuggestedResolution,
)
from src.schemas.lease import Lease


# System prompt for the conflict detection agent
CONFLICT_DETECTOR_SYSTEM_PROMPT = """You are an expert commercial real estate analyst 
specializing in lease conflict detection. Your role is to identify contradictions, 
inconsistencies, and conflicts between lease documents and their amendments.

You have access to memory of previously analyzed documents, allowing you to compare
terms across the entire document set.

When analyzing documents, look for:
1. TERM CONFLICTS: Contradicting dates (commencement, expiration, option dates)
2. RENT CONFLICTS: Inconsistent rent amounts, escalation schedules, or calculations
3. PARTY CONFLICTS: Mismatched party names or entity information
4. PROPERTY CONFLICTS: Inconsistent square footage, addresses, or premises descriptions
5. OPTION CONFLICTS: Contradicting renewal/termination options
6. CLAUSE CONFLICTS: Superseded clauses that aren't clearly addressed

For each conflict, determine:
- Severity (critical, high, medium, low, info)
- Which document should take precedence
- Suggested resolution

Always provide clear evidence with specific document references."""


CONFLICT_DETECTOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", CONFLICT_DETECTOR_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


class DocumentMemory:
    """
    In-memory storage for analyzed documents.
    
    Maintains a registry of base leases and amendments with their
    extracted data for cross-document conflict detection.
    
    Attributes:
        leases: Dictionary of lease_id -> Lease data
        amendments: Dictionary of amendment_id -> Amendment data
        relationships: Mapping of base leases to their amendments
    """
    
    def __init__(self) -> None:
        """Initialize empty document memory."""
        self.leases: dict[str, Lease] = {}
        self.amendments: dict[str, Amendment] = {}
        self.relationships: dict[str, list[str]] = {}  # lease_id -> [amendment_ids]
    
    def add_lease(self, lease: Lease) -> None:
        """Add a lease to memory."""
        self.leases[lease.document_id] = lease
        if lease.document_id not in self.relationships:
            self.relationships[lease.document_id] = []
    
    def add_amendment(self, amendment: Amendment, base_lease_id: str) -> None:
        """Add an amendment to memory with its base lease relationship."""
        self.amendments[amendment.document_id] = amendment
        if base_lease_id in self.relationships:
            self.relationships[base_lease_id].append(amendment.document_id)
    
    def get_lease_with_amendments(self, lease_id: str) -> tuple[Optional[Lease], list[Amendment]]:
        """Get a lease and all its amendments."""
        lease = self.leases.get(lease_id)
        amendment_ids = self.relationships.get(lease_id, [])
        amendments = [self.amendments[aid] for aid in amendment_ids if aid in self.amendments]
        return lease, amendments
    
    def clear(self) -> None:
        """Clear all document memory."""
        self.leases.clear()
        self.amendments.clear()
        self.relationships.clear()


class ConflictDetectorAgent:
    """
    Agent with memory for detecting conflicts between lease documents.
    
    Uses LangChain memory to maintain context across document analysis
    and identify contradictions between base leases and amendments.
    
    Example:
        >>> detector = ConflictDetectorAgent()
        >>> detector.add_lease(base_lease)
        >>> detector.add_amendment(amendment, base_lease.document_id)
        >>> report = detector.detect_conflicts(base_lease.document_id)
        >>> print(f"Found {report.total_conflicts} conflicts")
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the Conflict Detector agent.
        
        Args:
            model_name: OpenAI model to use (defaults to settings)
            temperature: LLM temperature (0 = deterministic)
            verbose: Enable verbose agent output
        """
        self.settings = get_settings()
        self.model_name = model_name or self.settings.openai_model
        self.temperature = temperature
        self.verbose = verbose
        
        # Document memory
        self.document_memory = DocumentMemory()
        
        # Conversation memory for the agent
        self.conversation_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )
        
        self._llm: Optional[ChatOpenAI] = None
        self._agent_executor: Optional[AgentExecutor] = None
    
    @property
    def llm(self) -> ChatOpenAI:
        """Get or create the LLM instance."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=self.settings.openai_api_key.get_secret_value(),
            )
        return self._llm
    
    def _create_tools(self) -> list[Tool]:
        """
        Create tools available to the conflict detection agent.
        
        Returns:
            List of LangChain tools for conflict analysis
        """
        tools = [
            Tool(
                name="compare_dates",
                description="Compare dates between documents to find conflicts",
                func=self._compare_dates,
            ),
            Tool(
                name="compare_rent",
                description="Compare rent amounts and escalations between documents",
                func=self._compare_rent,
            ),
            Tool(
                name="compare_parties",
                description="Compare party information between documents",
                func=self._compare_parties,
            ),
            Tool(
                name="compare_property",
                description="Compare property details between documents",
                func=self._compare_property,
            ),
            Tool(
                name="check_superseded_terms",
                description="Check if amendment properly supersedes original terms",
                func=self._check_superseded_terms,
            ),
            Tool(
                name="validate_calculations",
                description="Validate financial calculations for consistency",
                func=self._validate_calculations,
            ),
        ]
        
        return tools
    
    def _compare_dates(self, documents: str) -> str:
        """Compare dates across documents for conflicts."""
        # TODO: Implement date comparison
        # - Check commencement dates
        # - Check expiration dates
        # - Check amendment effective dates
        # - Verify chronological ordering
        raise NotImplementedError("Date comparison not yet implemented")
    
    def _compare_rent(self, documents: str) -> str:
        """Compare rent terms across documents."""
        # TODO: Implement rent comparison
        # - Check base rent amounts
        # - Verify escalation schedules
        # - Compare rent per square foot calculations
        raise NotImplementedError("Rent comparison not yet implemented")
    
    def _compare_parties(self, documents: str) -> str:
        """Compare party information across documents."""
        # TODO: Implement party comparison
        # - Check for name changes
        # - Verify entity types
        # - Track assignments
        raise NotImplementedError("Party comparison not yet implemented")
    
    def _compare_property(self, documents: str) -> str:
        """Compare property details across documents."""
        # TODO: Implement property comparison
        # - Check square footage
        # - Compare addresses
        # - Track premises changes
        raise NotImplementedError("Property comparison not yet implemented")
    
    def _check_superseded_terms(self, documents: str) -> str:
        """Check if amendments properly supersede original terms."""
        # TODO: Implement supersession checking
        # - Identify modified terms
        # - Verify explicit supersession language
        # - Flag unclear modifications
        raise NotImplementedError("Supersession check not yet implemented")
    
    def _validate_calculations(self, documents: str) -> str:
        """Validate financial calculations for consistency."""
        # TODO: Implement calculation validation
        # - Verify rent calculations
        # - Check CAM calculations
        # - Validate escalation math
        raise NotImplementedError("Calculation validation not yet implemented")
    
    def _build_agent_executor(self) -> AgentExecutor:
        """
        Build the agent executor with memory.
        
        Returns:
            Configured AgentExecutor for conflict detection
        """
        tools = self._create_tools()
        
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=tools,
            prompt=CONFLICT_DETECTOR_PROMPT,
        )
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            memory=self.conversation_memory,
            verbose=self.verbose,
            handle_parsing_errors=True,
            max_iterations=15,
        )
    
    @property
    def agent_executor(self) -> AgentExecutor:
        """Get or create the agent executor."""
        if self._agent_executor is None:
            self._agent_executor = self._build_agent_executor()
        return self._agent_executor
    
    def add_lease(self, lease: Lease) -> None:
        """
        Add a lease to the document memory.
        
        Args:
            lease: Extracted lease data
        """
        self.document_memory.add_lease(lease)
    
    def add_amendment(self, amendment: Amendment, base_lease_id: str) -> None:
        """
        Add an amendment to the document memory.
        
        Args:
            amendment: Extracted amendment data
            base_lease_id: ID of the base lease being amended
        """
        self.document_memory.add_amendment(amendment, base_lease_id)
    
    def _create_conflict(
        self,
        category: ConflictCategory,
        severity: ConflictSeverity,
        field_name: str,
        description: str,
        source_a: DocumentReference,
        source_b: DocumentReference,
        value_a: Optional[str] = None,
        value_b: Optional[str] = None,
    ) -> Conflict:
        """
        Create a conflict record.
        
        Args:
            category: Conflict category
            severity: Conflict severity
            field_name: Name of conflicting field
            description: Human-readable description
            source_a: First document reference
            source_b: Second document reference
            value_a: Value from first document
            value_b: Value from second document
            
        Returns:
            Conflict object with all details
        """
        evidence = ConflictEvidence(
            source_a=source_a,
            source_b=source_b,
            value_a=value_a,
            value_b=value_b,
            explanation=description,
        )
        
        return Conflict(
            conflict_id=str(uuid4()),
            category=category,
            severity=severity,
            field_name=field_name,
            description=description,
            evidence=evidence,
            detected_at=datetime.utcnow(),
        )
    
    def detect_conflicts(self, lease_id: str) -> ConflictReport:
        """
        Detect conflicts for a lease and its amendments.
        
        Args:
            lease_id: ID of the base lease to analyze
            
        Returns:
            ConflictReport with all detected conflicts
            
        Raises:
            ValueError: If lease_id is not found in memory
        """
        lease, amendments = self.document_memory.get_lease_with_amendments(lease_id)
        
        if lease is None:
            raise ValueError(f"Lease {lease_id} not found in memory")
        
        # TODO: Implement full conflict detection logic
        # 1. Compare base lease with each amendment
        # 2. Compare amendments with each other (in order)
        # 3. Run agent for complex conflict detection
        # 4. Aggregate all conflicts into report
        
        raise NotImplementedError("Conflict detection not yet implemented")
    
    async def detect_conflicts_async(self, lease_id: str) -> ConflictReport:
        """
        Async version of detect_conflicts.
        
        Args:
            lease_id: ID of the base lease to analyze
            
        Returns:
            ConflictReport with all detected conflicts
        """
        # TODO: Implement async conflict detection
        raise NotImplementedError("Async conflict detection not yet implemented")
    
    def get_conflict_summary(self, report: ConflictReport) -> dict:
        """
        Generate a summary of conflicts by severity and category.
        
        Args:
            report: Conflict report to summarize
            
        Returns:
            Dictionary with conflict counts by severity and category
        """
        summary = {
            "total": report.total_conflicts,
            "by_severity": {},
            "by_category": {},
            "unresolved": len(report.unresolved_conflicts),
        }
        
        for severity in ConflictSeverity:
            count = len(report.get_conflicts_by_severity(severity))
            if count > 0:
                summary["by_severity"][severity.value] = count
        
        for category in ConflictCategory:
            count = len(report.get_conflicts_by_category(category))
            if count > 0:
                summary["by_category"][category.value] = count
        
        return summary
    
    def clear_memory(self) -> None:
        """Clear all document and conversation memory."""
        self.document_memory.clear()
        self.conversation_memory.clear()


# TODO: Add persistence for document memory (database/file storage)
# TODO: Add support for incremental conflict detection
# TODO: Add conflict resolution workflow
# TODO: Add integration with notification systems
# TODO: Add conflict history and audit trail
