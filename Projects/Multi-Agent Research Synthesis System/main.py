import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from config import Config
from research_agent_system import ResearchSynthesisWorkflow


def print_banner():
    banner = """
        Multi-Agent Research Synthesis System
        Powered by LangGraph, GPT-4, Claude Sonnet & FAISS
    """
    print(banner)


def save_results(result: dict, output_path: Optional[str] = None):
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"research_synthesis_{timestamp}.json"

    output = {
        "query": result["query"],
        "final_synthesis": result["final_output"],
        "quality_score": result["quality_score"],
        "iterations": result["iteration"],
        "papers_analyzed": len(result["papers"]),
        "papers": result["papers"],
        "search_plan": result["search_plan"],
        "critique": result["critique"],
        "timestamp": datetime.now().isoformat()
    }

    output_file = Path(output_path)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file.absolute()}")
    return output_file


def print_results(result: dict):
    print("\n" + "=" * 80)
    print("RESEARCH SYNTHESIS RESULTS")
    print("=" * 80)

    print(f"\nQuery: {result['query']}")
    print(f"Quality Score: {result['quality_score']:.1f}/10")
    print(f"Iterations: {result['iteration']}")
    print(f"Papers Analyzed: {len(result['papers'])}")

    print("\n" + "-" * 80)
    print("FINAL SYNTHESIS")
    print("-" * 80)
    print(result['final_output'])

    if result['papers']:
        print("\n" + "-" * 80)
        print("PAPERS REFERENCED")
        print("-" * 80)
        for i, paper in enumerate(result['papers'][:5], 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   Authors: {', '.join(paper['authors'][:3])}")
            print(f"   Published: {paper['published']}")
            print(f"   URL: {paper['url']}")

    print("\n" + "=" * 80 + "\n")


def interactive_mode():
    print_banner()
    print("Interactive Mode - Type 'quit' to exit\n")

    workflow = ResearchSynthesisWorkflow()

    while True:
        try:
            query = input("Enter research query: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if not query:
                print("Please enter a valid query\n")
                continue

            iterations_input = input(
                f"Max iterations (default {Config.MAX_ITERATIONS}): "
            ).strip()
            max_iterations = (
                int(iterations_input)
                if iterations_input.isdigit()
                else Config.MAX_ITERATIONS
            )

            print("\nStarting analysis...\n")

            result = workflow.run(query, max_iterations=max_iterations)
            print_results(result)

            save_choice = input("Save results? (y/n): ").strip().lower()
            if save_choice == 'y':
                save_results(result)

            print("\n" + "-" * 80 + "\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
            continue


def batch_mode(input_file: str, output_dir: str = "output"):
    print_banner()
    print(f"Batch Mode - Processing queries from {input_file}\n")

    with open(input_file, 'r') as f:
        queries = [line.strip() for line in f if line.strip()]

    if not queries:
        print("No queries found in input file")
        return

    print(f"Found {len(queries)} queries to process\n")

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    workflow = ResearchSynthesisWorkflow()

    results = []
    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Processing Query {i}/{len(queries)}")
        print(f"{'=' * 80}\n")

        try:
            result = workflow.run(query, max_iterations=Config.MAX_ITERATIONS)
            results.append(result)

            output_file = output_path / f"result_{i:03d}.json"
            save_results(result, str(output_file))

        except Exception as e:
            print(f"Error processing query {i}: {e}")
            continue

    summary = {
        "total_queries": len(queries),
        "successful": len(results),
        "failed": len(queries) - len(results),
        "average_quality": (
            sum(r['quality_score'] for r in results) / len(results)
            if results else 0
        ),
        "timestamp": datetime.now().isoformat()
    }

    with open(output_path / "batch_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'=' * 80}")
    print("Batch processing complete")
    print(f"Processed: {len(results)}/{len(queries)} queries")
    print(f"Results saved to: {output_path.absolute()}")
    print(f"{'=' * 80}\n")


def single_query_mode(query: str, output: Optional[str] = None, iterations: int = 2):
    print_banner()

    workflow = ResearchSynthesisWorkflow()

    print(f"Processing query: {query}\n")
    result = workflow.run(query, max_iterations=iterations)

    print_results(result)

    if output:
        save_results(result, output)
    else:
        save_results(result)


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Research Synthesis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py -i
  python main.py -q "What are the latest techniques for RAG?"
  python main.py -b queries.txt -o results/
  python main.py -q "LLM hallucination mitigation" -n 3 -o result.json
  python main.py -q "Multi-agent systems" --langsmith
        """
    )

    parser.add_argument('-i', '--interactive', action='store_true')
    parser.add_argument('-q', '--query', type=str)
    parser.add_argument('-b', '--batch', type=str)
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument(
        '-n', '--iterations',
        type=int,
        default=Config.MAX_ITERATIONS
    )
    parser.add_argument('--langsmith', action='store_true')

    args = parser.parse_args()

    if args.langsmith:
        Config.enable_langsmith()
        print("LangSmith tracing enabled\n")

    if args.interactive:
        interactive_mode()
    elif args.query:
        single_query_mode(args.query, args.output, args.iterations)
    elif args.batch:
        output_dir = args.output or "output"
        batch_mode(args.batch, output_dir)
    else:
        interactive_mode()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
