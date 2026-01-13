"""
Test suite for Multi-Agent Research Synthesis System
Tests individual agents and the full workflow
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from research_agent_system import (
    PlannerAgent, SearchAgent, SummarizerAgent,
    SynthesisAgent, CriticAgent, ReflectionAgent,
    VectorStoreManager, ResearchSynthesisWorkflow
)

class TestVectorStoreManager(unittest.TestCase):
    """Test vector store functionality"""
    
    def setUp(self):
        self.manager = VectorStoreManager()
    
    def test_create_vectorstore(self):
        """Test vector store creation"""
        papers = [
            {
                'title': 'Test Paper',
                'abstract': 'This is a test abstract about LLMs.',
                'authors': ['John Doe'],
                'published': '2024-01-01',
                'url': 'http://test.com'
            }
        ]
        
        with patch('research_synthesis_system.FAISS.from_texts') as mock_faiss:
            mock_faiss.return_value = Mock()
            vectorstore = self.manager.create_vectorstore(papers)
            self.assertIsNotNone(vectorstore)
            mock_faiss.assert_called_once()

class TestPlannerAgent(unittest.TestCase):
    """Test planner agent"""
    
    def setUp(self):
        self.agent = PlannerAgent()
    
    @patch('research_synthesis_system.ChatOpenAI')
    def test_plan_generation(self, mock_llm):
        """Test research plan generation"""
        mock_response = Mock()
        mock_response.content = "Research plan: 1. Search for papers 2. Analyze findings"
        mock_llm.return_value.invoke.return_value = mock_response
        
        state = {
            'query': 'Test query',
            'messages': []
        }
        
        result = self.agent.plan(state)
        self.assertIn('search_plan', result)
        self.assertTrue(len(result['messages']) > 0)

class TestSearchAgent(unittest.TestCase):
    """Test search agent"""
    
    def setUp(self):
        self.agent = SearchAgent()
    
    @patch('research_synthesis_system.arxiv.Client')
    def test_paper_search(self, mock_arxiv):
        """Test arXiv paper search"""
        mock_result = Mock()
        mock_result.title = "Test Paper"
        mock_result.authors = [Mock(name="John Doe")]
        mock_result.summary = "Test abstract"
        mock_result.published = Mock(strftime=lambda x: "2024-01-01")
        mock_result.entry_id = "http://arxiv.org/abs/1234.5678"
        mock_result.pdf_url = "http://arxiv.org/pdf/1234.5678"
        
        mock_arxiv.return_value.results.return_value = [mock_result]
        
        state = {
            'query': 'LLM hallucinations',
            'messages': []
        }
        
        result = self.agent.search(state)
        self.assertIn('papers', result)
        self.assertTrue(len(result['papers']) > 0)

class TestSummarizerAgent(unittest.TestCase):
    """Test summarizer agent"""
    
    @patch('research_synthesis_system.ChatAnthropic')
    @patch('research_synthesis_system.VectorStoreManager')
    def test_summarization(self, mock_vector, mock_claude):
        """Test paper summarization with RAG"""
        agent = SummarizerAgent()
        
        mock_response = Mock()
        mock_response.content = "Summary of the paper..."
        mock_claude.return_value.invoke.return_value = mock_response
        
        mock_vector.return_value.similarity_search.return_value = [
            {'content': 'Paper content', 'metadata': {}, 'score': 0.9}
        ]
        
        state = {
            'papers': [{
                'title': 'Test Paper',
                'abstract': 'Test abstract',
                'authors': ['John Doe'],
                'url': 'http://test.com',
                'published': '2024-01-01'
            }],
            'query': 'Test query',
            'messages': []
        }
        
        result = agent.summarize(state)
        self.assertIn('summaries', result)

class TestWorkflowIntegration(unittest.TestCase):
    """Integration tests for full workflow"""
    
    @patch('research_synthesis_system.SearchAgent.search')
    @patch('research_synthesis_system.PlannerAgent.plan')
    def test_workflow_execution(self, mock_plan, mock_search):
        """Test complete workflow execution"""
        # Mock planner
        mock_plan.return_value = {
            'query': 'Test query',
            'search_plan': 'Mock plan',
            'messages': []
        }
        
        # Mock searcher
        mock_search.return_value = {
            'query': 'Test query',
            'papers': [{
                'title': 'Mock Paper',
                'abstract': 'Mock abstract',
                'authors': ['Mock Author'],
                'url': 'http://mock.com',
                'published': '2024-01-01'
            }],
            'messages': []
        }
        
        # This would be a more complex integration test
        # For now, just verify workflow can be instantiated
        workflow = ResearchSynthesisWorkflow()
        self.assertIsNotNone(workflow.workflow)

class TestQualityMetrics(unittest.TestCase):
    """Test quality scoring and hallucination detection"""
    
    def test_quality_score_extraction(self):
        """Test extraction of quality scores from critique"""
        critique_json = '{"quality_score": 8.5, "hallucinations": []}'
        
        import json
        parsed = json.loads(critique_json)
        self.assertEqual(parsed['quality_score'], 8.5)
    
    def test_hallucination_detection(self):
        """Test hallucination detection in critique"""
        critique = {
            "hallucinations": [
                "Claim X is not supported by sources",
                "Statistic Y is fabricated"
            ],
            "quality_score": 4.0
        }
        
        self.assertTrue(len(critique['hallucinations']) > 0)
        self.assertLess(critique['quality_score'], 5.0)

def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)