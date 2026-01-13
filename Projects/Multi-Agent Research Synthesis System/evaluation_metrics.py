"""
Evaluation metrics and analysis tools for Research Synthesis System
Measures hallucination rates, quality scores, and system performance
"""

import json
import re
from typing import List, Dict, Any
from collections import Counter
import numpy as np
from datetime import datetime

class EvaluationMetrics:
    """Comprehensive evaluation metrics for the system"""
    
    def __init__(self):
        self.results = []
    
    def add_result(self, result: Dict[str, Any]):
        """Add a result for evaluation"""
        self.results.append(result)
    
    def calculate_quality_metrics(self) -> Dict[str, float]:
        """Calculate quality metrics across all results"""
        if not self.results:
            return {}
        
        quality_scores = [r['quality_score'] for r in self.results]
        iterations = [r['iteration'] for r in self.results]
        papers_analyzed = [len(r['papers']) for r in self.results]
        
        metrics = {
            'avg_quality_score': np.mean(quality_scores),
            'std_quality_score': np.std(quality_scores),
            'min_quality_score': np.min(quality_scores),
            'max_quality_score': np.max(quality_scores),
            'avg_iterations': np.mean(iterations),
            'avg_papers_analyzed': np.mean(papers_analyzed),
            'total_queries': len(self.results),
            'high_quality_rate': sum(1 for s in quality_scores if s >= 8.0) / len(quality_scores),
            'low_quality_rate': sum(1 for s in quality_scores if s < 6.0) / len(quality_scores),
        }
        
        return metrics
    
    def analyze_hallucinations(self) -> Dict[str, Any]:
        """Analyze hallucination patterns"""
        hallucination_counts = []
        hallucination_types = Counter()
        
        for result in self.results:
            critique = result.get('critique', '')
            
            # Try to parse critique as JSON
            try:
                if isinstance(critique, str):
                    critique_json = json.loads(critique)
                else:
                    critique_json = critique
                
                hallucinations = critique_json.get('hallucinations', [])
                hallucination_counts.append(len(hallucinations))
                
                # Categorize hallucinations
                for h in hallucinations:
                    if 'unsupported' in h.lower() or 'not found' in h.lower():
                        hallucination_types['unsupported_claim'] += 1
                    elif 'fabricate' in h.lower() or 'made up' in h.lower():
                        hallucination_types['fabricated_data'] += 1
                    elif 'contradict' in h.lower():
                        hallucination_types['contradiction'] += 1
                    else:
                        hallucination_types['other'] += 1
            except:
                # Extract from text if JSON parsing fails
                hallucination_indicators = [
                    'hallucination', 'unsupported', 'fabricated',
                    'not found in sources', 'no evidence'
                ]
                count = sum(critique.lower().count(indicator) for indicator in hallucination_indicators)
                hallucination_counts.append(count)
        
        return {
            'avg_hallucinations_per_query': np.mean(hallucination_counts) if hallucination_counts else 0,
            'total_hallucinations': sum(hallucination_counts),
            'hallucination_types': dict(hallucination_types),
            'zero_hallucination_rate': sum(1 for c in hallucination_counts if c == 0) / len(hallucination_counts) if hallucination_counts else 0
        }
    
    def analyze_improvement_rate(self) -> Dict[str, float]:
        """Analyze how reflection improves quality"""
        improvements = []
        
        for result in self.results:
            if result['iteration'] > 0:
                # Quality improved through reflection
                improvements.append(1)
            else:
                improvements.append(0)
        
        return {
            'reflection_usage_rate': np.mean(improvements) if improvements else 0,
            'avg_improvement_iterations': np.mean([r['iteration'] for r in self.results])
        }
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive evaluation report"""
        quality_metrics = self.calculate_quality_metrics()
        hallucination_analysis = self.analyze_hallucinations()
        improvement_analysis = self.analyze_improvement_rate()
        
        report = f"""
╔═══════════════════════════════════════════════════════════════════════╗
║                    SYSTEM EVALUATION REPORT                           ║
║                    Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                     ║
╚═══════════════════════════════════════════════════════════════════════╝

📊 QUALITY METRICS
──────────────────────────────────────────────────────────────────────
Total Queries Processed:        {quality_metrics.get('total_queries', 0)}
Average Quality Score:          {quality_metrics.get('avg_quality_score', 0):.2f}/10
Quality Score Std Dev:          {quality_metrics.get('std_quality_score', 0):.2f}
Min/Max Quality Score:          {quality_metrics.get('min_quality_score', 0):.1f} / {quality_metrics.get('max_quality_score', 0):.1f}
High Quality Rate (≥8.0):       {quality_metrics.get('high_quality_rate', 0)*100:.1f}%
Low Quality Rate (<6.0):        {quality_metrics.get('low_quality_rate', 0)*100:.1f}%

📚 ANALYSIS METRICS
──────────────────────────────────────────────────────────────────────
Avg Papers Analyzed:            {quality_metrics.get('avg_papers_analyzed', 0):.1f}
Avg Reflection Iterations:      {quality_metrics.get('avg_iterations', 0):.1f}
Reflection Usage Rate:          {improvement_analysis.get('reflection_usage_rate', 0)*100:.1f}%

🔍 HALLUCINATION ANALYSIS
──────────────────────────────────────────────────────────────────────
Total Hallucinations Detected:  {hallucination_analysis.get('total_hallucinations', 0)}
Avg Hallucinations per Query:   {hallucination_analysis.get('avg_hallucinations_per_query', 0):.2f}
Zero Hallucination Rate:        {hallucination_analysis.get('zero_hallucination_rate', 0)*100:.1f}%

Hallucination Types:
"""
        
        for h_type, count in hallucination_analysis.get('hallucination_types', {}).items():
            report += f"  - {h_type.replace('_', ' ').title()}: {count}\n"
        
        report += """
══════════════════════════════════════════════════════════════════════

INTERPRETATION
──────────────────────────────────────────────────────────────────────
"""
        
        avg_quality = quality_metrics.get('avg_quality_score', 0)
        if avg_quality >= 8.0:
            report += "✅ EXCELLENT: System consistently produces high-quality synthesis\n"
        elif avg_quality >= 7.0:
            report += "✓ GOOD: System meets quality threshold with room for improvement\n"
        elif avg_quality >= 6.0:
            report += "⚠ ACCEPTABLE: System needs optimization\n"
        else:
            report += "❌ POOR: System requires significant improvements\n"
        
        hal_rate = hallucination_analysis.get('zero_hallucination_rate', 0)
        if hal_rate >= 0.8:
            report += "✅ EXCELLENT: Very low hallucination rate\n"
        elif hal_rate >= 0.6:
            report += "✓ GOOD: Acceptable hallucination control\n"
        else:
            report += "⚠ NEEDS IMPROVEMENT: High hallucination rate\n"
        
        report += "\n══════════════════════════════════════════════════════════════════════\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
                
                # Also save detailed metrics as JSON
                json_data = {
                    'quality_metrics': quality_metrics,
                    'hallucination_analysis': hallucination_analysis,
                    'improvement_analysis': improvement_analysis,
                    'timestamp': datetime.now().isoformat()
                }
                json_file = output_file.replace('.txt', '_detailed.json')
                with open(json_file, 'w') as jf:
                    json.dump(json_data, jf, indent=2)
        
        return report

class PerformanceBenchmark:
    """Benchmark system performance"""
    
    def __init__(self):
        self.timings = []
    
    def add_timing(self, query: str, duration: float, papers_count: int):
        """Add timing data"""
        self.timings.append({
            'query': query,
            'duration': duration,
            'papers_count': papers_count,
            'papers_per_second': papers_count / duration if duration > 0 else 0
        })
    
    def calculate_performance_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        if not self.timings:
            return {}
        
        durations = [t['duration'] for t in self.timings]
        papers_per_sec = [t['papers_per_second'] for t in self.timings]
        
        return {
            'avg_duration_seconds': np.mean(durations),
            'min_duration_seconds': np.min(durations),
            'max_duration_seconds': np.max(durations),
            'avg_papers_per_second': np.mean(papers_per_sec),
            'total_queries': len(self.timings)
        }

def compare_iterations(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare quality improvements across iterations"""
    
    by_iteration = {}
    for result in results:
        iter_count = result['iteration']
        if iter_count not in by_iteration:
            by_iteration[iter_count] = []
        by_iteration[iter_count].append(result['quality_score'])
    
    comparison = {}
    for iteration, scores in by_iteration.items():
        comparison[f'iteration_{iteration}'] = {
            'avg_score': np.mean(scores),
            'count': len(scores)
        }
    
    return comparison

# Example usage
if __name__ == "__main__":
    # Load results from files
    import glob
    
    evaluator = EvaluationMetrics()
    
    # Load all result files
    for file_path in glob.glob("output/result_*.json"):
        with open(file_path, 'r') as f:
            result = json.load(f)
            evaluator.add_result(result)
    
    # Generate report
    report = evaluator.generate_report("evaluation_report.txt")
    print(report)