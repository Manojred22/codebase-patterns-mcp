"""
RAG Evaluation Framework
Complete toolkit for measuring RAG system performance
"""

import json
import time
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict

# ============================================================================
# 1. TEST DATA STRUCTURES
# ============================================================================

@dataclass
class TestQuery:
    """Single test query with ground truth"""
    id: int
    query: str
    relevant_files: List[str]  # Ground truth
    category: str  # e.g., "authentication", "database", "api"
    difficulty: str  # "easy", "medium", "hard"

@dataclass
class RetrievalResult:
    """Result from vector search"""
    file_path: str
    chunk_content: str
    score: float
    metadata: Dict

# ============================================================================
# 2. CREATE TEST DATASET
# ============================================================================

def create_test_dataset() -> List[TestQuery]:
    """
    Create your test queries with ground truth.
    Run this ONCE at the start, manually curate.
    """
    test_queries = [
        TestQuery(
            id=1,
            query="How do we validate JWT tokens?",
            relevant_files=[
                "src/auth/jwt.go",
                "src/middleware/auth.js",
                "src/utils/token-validator.py"
            ],
            category="authentication",
            difficulty="medium"
        ),
        TestQuery(
            id=2,
            query="Where is database connection pooling configured?",
            relevant_files=[
                "config/database.yaml",
                "src/db/connection_pool.go",
                "src/db/postgres.js"
            ],
            category="database",
            difficulty="easy"
        ),
        TestQuery(
            id=3,
            query="Show me error handling patterns for API calls",
            relevant_files=[
                "src/api/error_handler.go",
                "src/middleware/error_middleware.js",
                "src/utils/api_errors.py",
                "docs/error_codes.md"
            ],
            category="error_handling",
            difficulty="hard"
        ),
        # Add 12-17 more queries...
    ]
    
    # Save to file for reuse
    with open('test_queries.json', 'w') as f:
        json.dump([q.__dict__ for q in test_queries], f, indent=2)
    
    return test_queries

# ============================================================================
# 3. METRIC CALCULATORS
# ============================================================================

class RetrievalMetrics:
    """Calculate retrieval performance metrics"""
    
    @staticmethod
    def recall_at_k(retrieved: List[str], 
                    relevant: List[str], 
                    k: int) -> float:
        """
        Calculate Recall@K
        
        Args:
            retrieved: List of retrieved file paths (in order)
            relevant: Ground truth relevant files
            k: Top K to consider
            
        Returns:
            Recall score (0.0 to 1.0)
        """
        if not relevant:
            return 0.0
            
        top_k = set(retrieved[:k])
        relevant_set = set(relevant)
        
        hits = len(top_k & relevant_set)
        recall = hits / len(relevant_set)
        
        return recall
    
    @staticmethod
    def precision_at_k(retrieved: List[str], 
                       relevant: List[str], 
                       k: int) -> float:
        """Calculate Precision@K"""
        if k == 0:
            return 0.0
            
        top_k = set(retrieved[:k])
        relevant_set = set(relevant)
        
        hits = len(top_k & relevant_set)
        precision = hits / k
        
        return precision
    
    @staticmethod
    def mean_reciprocal_rank(retrieved: List[str], 
                            relevant: List[str]) -> float:
        """
        Calculate MRR - rank of first relevant result
        """
        relevant_set = set(relevant)
        
        for rank, doc in enumerate(retrieved, 1):
            if doc in relevant_set:
                return 1.0 / rank
        
        return 0.0  # No relevant doc found
    
    @staticmethod
    def ndcg_at_k(retrieved: List[str],
                  relevant: List[str],
                  k: int) -> float:
        """
        Normalized Discounted Cumulative Gain
        Accounts for position - higher relevance at top = better
        """
        def dcg(relevances: List[int], k: int) -> float:
            return sum(rel / np.log2(i + 2) 
                      for i, rel in enumerate(relevances[:k]))
        
        # Binary relevance: 1 if in relevant set, 0 otherwise
        relevances = [1 if doc in relevant else 0 
                     for doc in retrieved[:k]]
        
        # Ideal DCG (all relevant docs at top)
        ideal_relevances = sorted(relevances, reverse=True)
        
        dcg_val = dcg(relevances, k)
        idcg_val = dcg(ideal_relevances, k)
        
        return dcg_val / idcg_val if idcg_val > 0 else 0.0

# ============================================================================
# 4. RELEVANCE SCORING
# ============================================================================

class RelevanceScorer:
    """Manual relevance scoring helper"""
    
    @staticmethod
    def interactive_scoring(query: str, 
                          results: List[RetrievalResult]) -> List[int]:
        """
        Interactive CLI for manually scoring relevance
        Returns list of scores (1-5) for each result
        """
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}\n")
        
        scores = []
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"File: {result.file_path}")
            print(f"Content preview:\n{result.chunk_content[:200]}...")
            print("\nRelevance scale:")
            print("5 = Directly answers query, highly relevant")
            print("4 = Relevant, provides useful context")
            print("3 = Somewhat relevant, tangentially related")
            print("2 = Marginally relevant, minor connection")
            print("1 = Not relevant")
            
            while True:
                try:
                    score = int(input("\nScore (1-5): "))
                    if 1 <= score <= 5:
                        scores.append(score)
                        break
                    print("Please enter 1-5")
                except ValueError:
                    print("Please enter a number")
        
        return scores
    
    @staticmethod
    def batch_scoring_template(query: str, 
                               results: List[RetrievalResult]) -> str:
        """
        Generate template for batch scoring (e.g., in spreadsheet)
        """
        lines = [f"Query: {query}\n"]
        lines.append("File Path | Preview | Score (1-5)")
        lines.append("-" * 80)
        
        for i, result in enumerate(results, 1):
            preview = result.chunk_content[:100].replace('\n', ' ')
            lines.append(f"{result.file_path} | {preview}... | ")
        
        return "\n".join(lines)

# ============================================================================
# 5. END-TO-END EVALUATION
# ============================================================================

class EndToEndEvaluator:
    """Compare RAG vs Baseline with Claude"""
    
    def __init__(self, anthropic_api_key: str):
        self.api_key = anthropic_api_key
    
    def run_baseline_test(self, 
                         questions: List[str]) -> List[Dict]:
        """
        Test Claude WITHOUT RAG context
        Returns responses for manual rating
        """
        results = []
        
        for q in questions:
            response = self._call_claude(q, context=None)
            results.append({
                'question': q,
                'response': response,
                'has_context': False
            })
        
        return results
    
    def run_rag_test(self,
                    questions: List[str],
                    rag_retrieval_fn) -> List[Dict]:
        """
        Test Claude WITH RAG context
        
        Args:
            rag_retrieval_fn: Function that takes query, returns context string
        """
        results = []
        
        for q in questions:
            # Get context from your RAG system
            context = rag_retrieval_fn(q)
            response = self._call_claude(q, context=context)
            
            results.append({
                'question': q,
                'response': response,
                'context': context,
                'has_context': True
            })
        
        return results
    
    def _call_claude(self, question: str, context: str = None) -> str:
        """Call Claude API"""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        if context:
            prompt = f"""Here is relevant code from the codebase:

{context}

Question: {question}

Please answer based on the provided code."""
        else:
            prompt = question
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
    
    @staticmethod
    def create_rating_template(results: List[Dict]) -> str:
        """
        Generate template for rating Claude responses
        """
        lines = ["# Claude Response Evaluation\n"]
        lines.append("Rate each response on 1-5 scale for:")
        lines.append("- Accuracy: Factually correct for YOUR codebase?")
        lines.append("- Completeness: Covers important aspects?")
        lines.append("- Specificity: References actual code vs generic?\n")
        lines.append("="*80 + "\n")
        
        for i, r in enumerate(results, 1):
            lines.append(f"\n## Question {i}")
            lines.append(f"**Q:** {r['question']}")
            lines.append(f"**Has Context:** {r['has_context']}")
            lines.append(f"\n**Response:**\n{r['response']}\n")
            lines.append("**Ratings:**")
            lines.append("- Accuracy: ___ /5")
            lines.append("- Completeness: ___ /5")
            lines.append("- Specificity: ___ /5")
            lines.append("- Average: ___ /5\n")
            lines.append("="*80)
        
        return "\n".join(lines)

# ============================================================================
# 6. PERFORMANCE METRICS
# ============================================================================

class PerformanceMetrics:
    """Measure latency and throughput"""
    
    @staticmethod
    def measure_retrieval_latency(retrieval_fn, 
                                  queries: List[str],
                                  k: int = 5) -> Dict:
        """
        Measure retrieval performance
        
        Returns:
            {
                'mean_latency_ms': float,
                'p50_latency_ms': float,
                'p95_latency_ms': float,
                'p99_latency_ms': float
            }
        """
        latencies = []
        
        for query in queries:
            start = time.time()
            _ = retrieval_fn(query, k=k)
            latency = (time.time() - start) * 1000  # ms
            latencies.append(latency)
        
        latencies.sort()
        n = len(latencies)
        
        return {
            'mean_latency_ms': sum(latencies) / n,
            'p50_latency_ms': latencies[int(n * 0.5)],
            'p95_latency_ms': latencies[int(n * 0.95)],
            'p99_latency_ms': latencies[int(n * 0.99)],
            'min_latency_ms': latencies[0],
            'max_latency_ms': latencies[-1]
        }

# ============================================================================
# 7. COMPLETE EVALUATION PIPELINE
# ============================================================================

class RAGEvaluator:
    """
    Complete evaluation pipeline
    Orchestrates all metrics
    """
    
    def __init__(self, test_queries: List[TestQuery]):
        self.test_queries = test_queries
        self.results = defaultdict(list)
    
    def evaluate_retrieval(self, 
                          rag_system,
                          k_values: List[int] = [1, 3, 5, 10]) -> Dict:
        """
        Evaluate retrieval metrics across all queries
        
        Args:
            rag_system: Your RAG system with .retrieve(query, k) method
            k_values: Different K values to test
            
        Returns:
            Aggregated metrics
        """
        metrics = defaultdict(lambda: defaultdict(list))
        
        for query in self.test_queries:
            # Get retrieval results
            retrieved = rag_system.retrieve(query.query, k=max(k_values))
            retrieved_files = [r.file_path for r in retrieved]
            
            # Calculate metrics for each K
            for k in k_values:
                recall = RetrievalMetrics.recall_at_k(
                    retrieved_files, query.relevant_files, k
                )
                precision = RetrievalMetrics.precision_at_k(
                    retrieved_files, query.relevant_files, k
                )
                
                metrics[f'recall@{k}'][query.category].append(recall)
                metrics[f'precision@{k}'][query.category].append(precision)
            
            # MRR (independent of K)
            mrr = RetrievalMetrics.mean_reciprocal_rank(
                retrieved_files, query.relevant_files
            )
            metrics['mrr'][query.category].append(mrr)
        
        # Aggregate results
        aggregated = {}
        for metric_name, category_scores in metrics.items():
            aggregated[metric_name] = {
                'overall': sum(sum(scores) for scores in category_scores.values()) / 
                          sum(len(scores) for scores in category_scores.values()),
                'by_category': {
                    cat: sum(scores) / len(scores)
                    for cat, scores in category_scores.items()
                }
            }
        
        return aggregated
    
    def generate_report(self, metrics: Dict) -> str:
        """Generate markdown report"""
        lines = ["# RAG Evaluation Report\n"]
        lines.append(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total Queries: {len(self.test_queries)}\n")
        
        lines.append("## Retrieval Metrics\n")
        for metric_name, values in metrics.items():
            lines.append(f"### {metric_name.upper()}")
            lines.append(f"Overall: {values['overall']:.3f}\n")
            lines.append("By Category:")
            for cat, score in values['by_category'].items():
                lines.append(f"- {cat}: {score:.3f}")
            lines.append("")
        
        # Target comparison
        lines.append("## Target Achievement\n")
        recall_5 = metrics.get('recall@5', {}).get('overall', 0)
        target_met = "✅ MET" if recall_5 >= 0.80 else "❌ MISSED"
        lines.append(f"Recall@5: {recall_5:.1%} (Target: 80%) {target_met}")
        
        return "\n".join(lines)

# ============================================================================
# 8. USAGE EXAMPLE
# ============================================================================

def main():
    """Example usage of evaluation framework"""
    
    # 1. Create test dataset
    print("Step 1: Creating test dataset...")
    test_queries = create_test_dataset()
    
    # 2. Initialize evaluator
    evaluator = RAGEvaluator(test_queries)
    
    # 3. Evaluate your RAG system
    print("\nStep 2: Evaluating retrieval...")
    # Your RAG system should implement .retrieve(query, k) method
    # from your_rag_system import MyRAG
    # rag = MyRAG()
    # metrics = evaluator.evaluate_retrieval(rag)
    
    # 4. Generate report
    # report = evaluator.generate_report(metrics)
    # print(report)
    
    # Save to file
    # with open('evaluation_report.md', 'w') as f:
    #     f.write(report)
    
    print("\n✓ Evaluation framework ready!")
    print("Next steps:")
    print("1. Fill in test_queries.json with your queries")
    print("2. Implement retrieval in your RAG system")
    print("3. Run evaluator.evaluate_retrieval()")
    print("4. Manually score relevance for subset")
    print("5. Run end-to-end Claude comparison")

if __name__ == "__main__":
    main()
