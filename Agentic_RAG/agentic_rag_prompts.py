QUERY_CLASSIFICATION_PROMPT = """Analyze the following user query and classify it.

User Query: {query}

Classify based on:
1. Query Type: simple_factual, complex_reasoning, comparison, multi_hop, summarization
2. Complexity: Rate from 1-10
3. Whether it requires decomposition into sub-queries
4. Provide reasoning for your classification

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
    "query_type": "simple_factual",
    "complexity": 5,
    "requires_decomposition": false,
    "reasoning": "explanation here"
}}"""


QUERY_DECOMPOSITION_PROMPT = """Decompose this complex query into simpler sub-queries.

User Query: {query}

Create sub-queries that:
1. Can be answered independently or with minimal dependencies
2. Are ordered logically
3. Together provide information to answer the original query

Respond ONLY with valid JSON (no markdown, no extra text):
{{
    "sub_queries": [
        {{"question": "sub-question 1", "order": 1, "dependencies": []}},
        {{"question": "sub-question 2", "order": 2, "dependencies": [1]}}
    ],
    "synthesis_instruction": "How to combine the answers"
}}"""


RETRIEVAL_EVALUATION_PROMPT = """Evaluate if these retrieved documents are sufficient to answer the query.

Query: {query}

Retrieved Documents:
{docs_text}

Evaluate:
1. Are documents sufficient? (true/false)
2. Relevance score for each document (0-1)
3. What information is missing if insufficient?
4. Confidence in your evaluation (0-1)

Respond ONLY with valid JSON (no markdown, no extra text):
{{
    "is_sufficient": true,
    "relevance_scores": [0.9, 0.8, 0.7, 0.6, 0.5],
    "missing_info": null,
    "confidence": 0.85
}}"""


ANSWER_GENERATION_PROMPT = """Answer the following question based ONLY on the provided documents.

Question: {query}

Retrieved Documents:
{docs_text}{context_str}

Instructions:
1. Provide a comprehensive answer based on the documents
2. Cite specific documents when making claims
3. If documents don't contain enough information, explicitly state what's missing
4. Be precise and factual
5. Do not add information not present in the documents

Answer:"""


GENERATION_EVALUATION_PROMPT = """Evaluate the quality of this generated answer.

Question: {query}

Generated Answer:
{answer}

Source Documents:
{docs_text}

Evaluate:
1. Is the answer accurate based on documents? (true/false)
2. Is the answer complete? (true/false)
3. Is the answer grounded in the documents (no hallucinations)? (true/false)
4. Does it need refinement? (true/false)
5. List any issues found
6. Confidence score (0-1)

Respond ONLY with valid JSON (no markdown, no extra text):
{{
    "is_accurate": true,
    "is_complete": true,
    "is_grounded": true,
    "needs_refinement": false,
    "issues": [],
    "confidence": 0.9
}}"""


ANSWER_REFINEMENT_PROMPT = """Refine the following answer to address the identified issues.

Question: {query}

Initial Answer:
{initial_answer}

Issues Identified:
{issues_text}

Source Documents:
{docs_text}

Instructions:
1. Address each issue mentioned
2. Ensure answer is grounded in documents
3. Improve completeness and accuracy
4. Maintain clarity and coherence

Refined Answer:"""
