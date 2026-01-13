

import os
from typing import TypedDict, Annotated, List, Dict, Any
from operator import add
import numpy as np
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import arxiv
from datetime import datetime
import json


class AgentState(TypedDict):
    """State shared across all agents in the graph"""
    query: str
    papers: List[Dict[str, Any]]
    search_plan: str
    summaries: List[Dict[str, Any]]
    synthesis: str
    critique: str
    reflection: str
    iteration: int
    max_iterations: int
    quality_score: float
    final_output: str
    messages: Annotated[List, add]






class VectorStoreManager:
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def create_vectorstore(self, papers: List[Dict[str, Any]]) -> FAISS:

        documents = []
        metadatas = []
        
        for paper in papers:
            # Combine title, abstract, and summary for better retrieval
            content = f"Title: {paper['title']}\n\nAbstract: {paper['abstract']}"
            chunks = self.text_splitter.split_text(content)
            
            for chunk in chunks:
                documents.append(chunk)
                metadatas.append({
                    'title': paper['title'],
                    'authors': ', '.join(paper['authors']),
                    'published': paper['published'],
                    'url': paper['url']
                })
        
        self.vectorstore = FAISS.from_texts(
            documents,
            self.embeddings,
            metadatas=metadatas
        )
        return self.vectorstore
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for relevant paper chunks"""
        if not self.vectorstore:
            return []
        
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [
            {
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': float(score)
            }
            for doc, score in results
        ]


class PlannerAgent:
    """Creates research plan and decomposes queries"""
    
    def __init__(self, model: str = "gpt-4"):
        self.llm = ChatOpenAI(model=model, temperature=0.3)
    
    def plan(self, state: AgentState) -> AgentState:
        """Generate search and analysis plan"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research planning expert. Given a research query, create a detailed plan for:
1. What specific aspects to search for
2. Key topics and subtopics to explore
3. How to synthesize findings
4. Success criteria for the analysis

Be specific and actionable."""),
            ("human", "Research Query: {query}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"query": state["query"]})
        
        state["search_plan"] = response.content
        state["messages"].append(AIMessage(
            content=f"PLANNER: Created research plan\n{response.content}"
        ))
        
        return state




class SearchAgent:
    """Searches and retrieves research papers"""
    
    def __init__(self):
        self.client = arxiv.Client()
    
    def search(self, state: AgentState) -> AgentState:
        """Search arXiv for relevant papers"""
        query = state["query"]
        
        # Extract key terms for search
        search_query = query.replace("?", "").strip()
        
        search = arxiv.Search(
            query=search_query,
            max_results=10,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = []
        for result in self.client.results(search):
            papers.append({
                'title': result.title,
                'authors': [author.name for author in result.authors],
                'abstract': result.summary,
                'published': result.published.strftime("%Y-%m-%d"),
                'url': result.entry_id,
                'pdf_url': result.pdf_url
            })
        
        state["papers"] = papers
        state["messages"].append(AIMessage(
            content=f"SEARCH AGENT: Found {len(papers)} relevant papers"
        ))
        
        return state





class SummarizerAgent:
    """Summarizes papers using RAG with Claude"""
    
    def __init__(self):
        self.llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.2)
        self.vector_manager = VectorStoreManager()
    
    def summarize(self, state: AgentState) -> AgentState:
        """Create detailed summaries using RAG"""
        papers = state["papers"]
        
        if not papers:
            state["summaries"] = []
            return state
        
        # Create vector store
        vectorstore = self.vector_manager.create_vectorstore(papers)
        
        summaries = []
        for paper in papers[:5]:  # Summarize top 5 papers
            # Retrieve relevant context
            relevant_chunks = self.vector_manager.similarity_search(
                paper['title'] + " " + state["query"],
                k=3
            )
            
            context = "\n\n".join([chunk['content'] for chunk in relevant_chunks])
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert research paper analyzer. Summarize the paper focusing on:
1. Main contributions and findings
2. Methodology used
3. Key results and implications
4. Relevance to the research query

Be concise but comprehensive. Use only information from the provided context."""),
                ("human", """Paper Title: {title}

Context from paper:
{context}

Research Query: {query}

Provide a structured summary.""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({
                "title": paper['title'],
                "context": context,
                "query": state["query"]
            })
            
            summaries.append({
                'paper_title': paper['title'],
                'summary': response.content,
                'authors': paper['authors'],
                'url': paper['url']
            })
        
        state["summaries"] = summaries
        state["messages"].append(AIMessage(
            content=f"SUMMARIZER: Analyzed {len(summaries)} papers using RAG"
        ))
        
        return state





class SynthesisAgent:
    """Synthesizes findings from multiple papers"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.4)
    
    def synthesize(self, state: AgentState) -> AgentState:
        """Create comprehensive synthesis"""
        summaries = state["summaries"]
        
        if not summaries:
            state["synthesis"] = "No papers found for synthesis."
            return state
        
        summaries_text = "\n\n".join([
            f"Paper {i+1}: {s['paper_title']}\n{s['summary']}"
            for i, s in enumerate(summaries)
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research synthesis expert. Given summaries of multiple papers:
1. Identify common themes and patterns
2. Highlight contradictions or debates
3. Synthesize key insights
4. Draw meaningful conclusions
5. Identify research gaps

Create a coherent narrative that answers the research query."""),
            ("human", """Research Query: {query}

Paper Summaries:
{summaries}

Research Plan Context:
{plan}

Provide a comprehensive synthesis with clear sections.""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "query": state["query"],
            "summaries": summaries_text,
            "plan": state["search_plan"]
        })
        
        state["synthesis"] = response.content
        state["messages"].append(AIMessage(
            content="SYNTHESIS AGENT: Created comprehensive synthesis"
        ))
        
        return state





class CriticAgent:
    """Critiques synthesis for hallucinations and quality"""
    
    def __init__(self):
        self.llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.1)
    
    def critique(self, state: AgentState) -> AgentState:
        """Perform critical evaluation with hallucination detection"""
        
        # Ground truth from papers
        ground_truth = "\n\n".join([
            f"Paper: {s['paper_title']}\nAuthors: {', '.join(s['authors'])}\n{s['summary']}"
            for s in state["summaries"]
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a critical evaluator specializing in hallucination detection. Analyze the synthesis against source papers:

1. FACTUAL ACCURACY: Check each claim against source papers
2. HALLUCINATION DETECTION: Identify any unsupported claims
3. COMPLETENESS: Are key findings missing?
4. COHERENCE: Is the logic sound?
5. QUALITY SCORE: Rate 0-10

Provide specific feedback with citations to source papers."""),
            ("human", """Synthesis to Evaluate:
{synthesis}

Source Papers (Ground Truth):
{ground_truth}

Research Query: {query}

Provide detailed critique in JSON format with:
- hallucinations: list of unsupported claims
- accuracy_issues: list of inaccuracies
- missing_points: important omissions
- strengths: what's done well
- quality_score: 0-10
- recommendations: specific improvements""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "synthesis": state["synthesis"],
            "ground_truth": ground_truth,
            "query": state["query"]
        })
        
        state["critique"] = response.content
        
        # Extract quality score
        try:
            critique_json = json.loads(response.content)
            state["quality_score"] = critique_json.get("quality_score", 5.0)
        except:
            # Try to extract score from text
            import re
            score_match = re.search(r'"quality_score":\s*(\d+\.?\d*)', response.content)
            if score_match:
                state["quality_score"] = float(score_match.group(1))
            else:
                state["quality_score"] = 5.0
        
        state["messages"].append(AIMessage(
            content=f" CRITIC: Evaluated synthesis (Quality: {state['quality_score']}/10)"
        ))
        
        return state








class ReflectionAgent:
    """Reflects on critique and improves synthesis"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    
    def reflect(self, state: AgentState) -> AgentState:
        """Improve synthesis based on critique"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a reflective agent that improves research synthesis. 
Given the original synthesis, critique, and source papers:
1. Address all identified issues
2. Remove hallucinations
3. Add missing information
4. Improve clarity and coherence
5. Ensure all claims are grounded in sources

Produce an improved version that maintains the same structure but fixes all issues."""),
            ("human", """Original Synthesis:
{synthesis}

Critique and Issues:
{critique}

Source Papers:
{summaries}

Create an improved synthesis that addresses all critique points.""")
        ])
        
        summaries_text = "\n\n".join([
            f"Paper: {s['paper_title']}\n{s['summary']}"
            for s in state["summaries"]
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "synthesis": state["synthesis"],
            "critique": state["critique"],
            "summaries": summaries_text
        })
        
        state["reflection"] = response.content
        state["synthesis"] = response.content  # Update synthesis
        state["iteration"] += 1
        
        state["messages"].append(AIMessage(
            content=f" REFLECTION: Improved synthesis (Iteration {state['iteration']})"
        ))
        
        return state


class ResearchSynthesisWorkflow:
    """Main workflow orchestrator using LangGraph"""
    
    def __init__(self):
        self.planner = PlannerAgent()
        self.searcher = SearchAgent()
        self.summarizer = SummarizerAgent()
        self.synthesizer = SynthesisAgent()
        self.critic = CriticAgent()
        self.reflector = ReflectionAgent()
        
        self.workflow = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the agent workflow graph"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("planner", self.planner.plan)
        workflow.add_node("searcher", self.searcher.search)
        workflow.add_node("summarizer", self.summarizer.summarize)
        workflow.add_node("synthesizer", self.synthesizer.synthesize)
        workflow.add_node("critic", self.critic.critique)
        workflow.add_node("reflector", self.reflector.reflect)
        
        # Define flow
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "searcher")
        workflow.add_edge("searcher", "summarizer")
        workflow.add_edge("summarizer", "synthesizer")
        workflow.add_edge("synthesizer", "critic")
        
        # Conditional edge: reflect if quality is low and iterations remain
        def should_reflect(state: AgentState) -> str:
            if state["quality_score"] < 7.0 and state["iteration"] < state["max_iterations"]:
                return "reflector"
            return "end"
        
        workflow.add_conditional_edges(
            "critic",
            should_reflect,
            {
                "reflector": "reflector",
                "end": END
            }
        )
        
        # Loop back from reflector to critic
        workflow.add_edge("reflector", "critic")
        
        return workflow.compile(checkpointer=MemorySaver())
    
    def run(self, query: str, max_iterations: int = 2) -> Dict[str, Any]:
        """Execute the research synthesis workflow"""
        
        initial_state = {
            "query": query,
            "papers": [],
            "search_plan": "",
            "summaries": [],
            "synthesis": "",
            "critique": "",
            "reflection": "",
            "iteration": 0,
            "max_iterations": max_iterations,
            "quality_score": 0.0,
            "final_output": "",
            "messages": []
        }
        
        print(f"\n{'='*80}")
        print(f"Starting Research Synthesis Workflow")
        print(f"Query: {query}")
        print(f"{'='*80}\n")
        
        # Run workflow
        config = {"configurable": {"thread_id": "research_synthesis"}}
        final_state = None
        
        for event in self.workflow.stream(initial_state, config):
            for node_name, node_state in event.items():
                if node_name != "__end__":
                    print(f"\n{'─'*80}")
                    if node_state["messages"]:
                        print(node_state["messages"][-1].content)
                final_state = node_state
        
        if final_state:
            final_state["final_output"] = final_state["synthesis"]
        
        print(f"\n{'='*80}")
        print(f"Workflow Complete")
        print(f"{'='*80}\n")
        
        return final_state



def main():
    """Main execution function"""
    
    # Set API keys (you'll need to set these environment variables)
    # os.environ["OPENAI_API_KEY"] = "your-key"
    # os.environ["ANTHROPIC_API_KEY"] = "your-key"
    
    # Initialize workflow
    workflow = ResearchSynthesisWorkflow()
    
    # Example research query
    query = "What are the latest techniques for mitigating hallucinations in Large Language Models?"
    
    # Run the workflow
    result = workflow.run(query, max_iterations=2)
    
    # Display final results
    print("\n" + "="*80)
    print("FINAL SYNTHESIS")
    print("="*80 + "\n")
    print(result["final_output"])
    
    print("\n" + "="*80)
    print(" QUALITY METRICS")
    print("="*80)
    print(f"Quality Score: {result['quality_score']}/10")
    print(f"Iterations: {result['iteration']}")
    print(f"Papers Analyzed: {len(result['papers'])}")
    
    # Save results
    output = {
        "query": result["query"],
        "final_synthesis": result["final_output"],
        "quality_score": result["quality_score"],
        "iterations": result["iteration"],
        "papers": result["papers"],
        "timestamp": datetime.now().isoformat()
    }
    
    with open("research_synthesis_output.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n Results saved to research_synthesis_output.json")

if __name__ == "__main__":
    main()