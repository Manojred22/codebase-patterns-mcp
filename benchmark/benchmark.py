#!/usr/bin/env python3
"""
MCP Benchmark Framework - Objective Measurable Testing
Compares workflows WITH vs WITHOUT MCP for codebase discovery tasks
"""

import time
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import statistics


@dataclass
class BenchmarkResult:
    """Single benchmark test result"""
    test_id: str
    query: str
    method: str  # "mcp" or "manual"
    timestamp: str

    # Timing metrics
    search_time_seconds: float
    total_time_seconds: float

    # Quality metrics
    results_found: int
    relevant_results: int  # User validates relevance
    precision: float  # relevant / found

    # Resource metrics
    api_calls: int
    cost_estimate_usd: float

    # User experience
    manual_steps_required: int
    files_manually_opened: int


class BenchmarkRunner:
    """Run and aggregate benchmark tests"""

    def __init__(self, output_dir: str = "./benchmark/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_mcp_search(self, query: str, limit: int = 5) -> BenchmarkResult:
        """Run search using MCP server"""
        print(f"\n🔍 MCP Search: '{query}'")

        start_time = time.time()

        # Run search
        cmd = f"source venv/bin/activate && python search_cli.py '{query}' --limit {limit}"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        search_time = time.time() - start_time

        # Parse results count
        results_found = 0
        if "Found" in result.stdout:
            for line in result.stdout.split('\n'):
                if "Found" in line and "results" in line:
                    try:
                        results_found = int(line.split("Found")[1].split("results")[0].strip())
                    except:
                        pass

        return BenchmarkResult(
            test_id=f"{self.session_id}_mcp_{int(time.time())}",
            query=query,
            method="mcp",
            timestamp=datetime.now().isoformat(),
            search_time_seconds=search_time,
            total_time_seconds=search_time,
            results_found=results_found,
            relevant_results=0,  # To be filled by user
            precision=0.0,
            api_calls=1,  # One embedding generation
            cost_estimate_usd=0.0001,  # ~$0.0001 per query
            manual_steps_required=1,  # Just run the query
            files_manually_opened=0
        )

    def run_manual_search(self, query: str, search_pattern: str) -> BenchmarkResult:
        """Simulate manual search (grep + manual file reading)"""
        print(f"\n📂 Manual Search: '{query}'")
        print(f"   Pattern: {search_pattern}")

        start_time = time.time()

        # Run grep search
        cmd = f"grep -r '{search_pattern}' repos/ --include='*.go' | head -20"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        search_time = time.time() - start_time

        # Count results
        results_found = len(result.stdout.split('\n')) if result.stdout else 0

        # Manual steps: grep + read each file + synthesize pattern
        manual_steps = 3 + results_found

        return BenchmarkResult(
            test_id=f"{self.session_id}_manual_{int(time.time())}",
            query=query,
            method="manual",
            timestamp=datetime.now().isoformat(),
            search_time_seconds=search_time,
            total_time_seconds=search_time + (results_found * 10),  # Assume 10s per file to read
            results_found=results_found,
            relevant_results=0,  # To be filled
            precision=0.0,
            api_calls=0,
            cost_estimate_usd=0.0,
            manual_steps_required=manual_steps,
            files_manually_opened=results_found
        )

    def save_result(self, result: BenchmarkResult):
        """Save individual result"""
        filename = self.output_dir / f"{result.test_id}.json"
        with open(filename, 'w') as f:
            json.dump(asdict(result), f, indent=2)
        print(f"   ✅ Saved: {filename}")

    def aggregate_results(self) -> Dict:
        """Aggregate all results and compute statistics"""
        all_results = []
        for file in self.output_dir.glob("*.json"):
            with open(file) as f:
                all_results.append(json.load(f))

        if not all_results:
            return {"error": "No results found"}

        # Separate by method
        mcp_results = [r for r in all_results if r['method'] == 'mcp']
        manual_results = [r for r in all_results if r['method'] == 'manual']

        def compute_stats(results: List[Dict], metric: str) -> Dict:
            values = [r[metric] for r in results if metric in r]
            if not values:
                return {"mean": 0, "median": 0, "min": 0, "max": 0}
            return {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0
            }

        summary = {
            "total_tests": len(all_results),
            "mcp_tests": len(mcp_results),
            "manual_tests": len(manual_results),
            "generated_at": datetime.now().isoformat(),

            "mcp_metrics": {
                "search_time": compute_stats(mcp_results, "search_time_seconds"),
                "total_time": compute_stats(mcp_results, "total_time_seconds"),
                "results_found": compute_stats(mcp_results, "results_found"),
                "manual_steps": compute_stats(mcp_results, "manual_steps_required"),
                "files_opened": compute_stats(mcp_results, "files_manually_opened"),
                "total_cost_usd": sum(r['cost_estimate_usd'] for r in mcp_results)
            },

            "manual_metrics": {
                "search_time": compute_stats(manual_results, "search_time_seconds"),
                "total_time": compute_stats(manual_results, "total_time_seconds"),
                "results_found": compute_stats(manual_results, "results_found"),
                "manual_steps": compute_stats(manual_results, "manual_steps_required"),
                "files_opened": compute_stats(manual_results, "files_manually_opened"),
                "total_cost_usd": 0.0
            }
        }

        # Calculate improvements
        if mcp_results and manual_results:
            mcp_time = summary["mcp_metrics"]["total_time"]["mean"]
            manual_time = summary["manual_metrics"]["total_time"]["mean"]

            summary["improvements"] = {
                "time_saved_seconds": manual_time - mcp_time,
                "time_saved_percent": ((manual_time - mcp_time) / manual_time * 100) if manual_time > 0 else 0,
                "speedup_factor": manual_time / mcp_time if mcp_time > 0 else 0,
                "steps_reduced": (
                    summary["manual_metrics"]["manual_steps"]["mean"] -
                    summary["mcp_metrics"]["manual_steps"]["mean"]
                ),
                "files_saved": summary["manual_metrics"]["files_opened"]["mean"]
            }

        return summary


def main():
    """Run benchmark suite"""
    runner = BenchmarkRunner()

    print("="*70)
    print("🏁 MCP BENCHMARK SUITE")
    print("="*70)

    # Define test queries
    test_cases = [
        {
            "query": "How are API endpoints structured?",
            "mcp_query": "API endpoint handler structure",
            "manual_pattern": "MakeHandler"
        },
        {
            "query": "How is JWT authentication implemented?",
            "mcp_query": "JWT authentication middleware",
            "manual_pattern": "JWT.*middleware"
        },
        {
            "query": "How are database transactions handled?",
            "mcp_query": "database transaction error handling",
            "manual_pattern": "transaction"
        },
        {
            "query": "What's the pattern for HTTP middleware?",
            "mcp_query": "HTTP request middleware",
            "manual_pattern": "middleware.*http"
        },
        {
            "query": "How do we validate user input?",
            "mcp_query": "user input validation",
            "manual_pattern": "Validate.*Request"
        }
    ]

    # Run tests
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_cases)}: {test['query']}")
        print(f"{'='*70}")

        # Run MCP search
        mcp_result = runner.run_mcp_search(test['mcp_query'])
        runner.save_result(mcp_result)

        # Run manual search
        manual_result = runner.run_manual_search(test['query'], test['manual_pattern'])
        runner.save_result(manual_result)

        time.sleep(1)  # Rate limiting

    # Generate summary
    print(f"\n{'='*70}")
    print("📊 GENERATING AGGREGATE REPORT")
    print(f"{'='*70}")

    summary = runner.aggregate_results()

    # Save summary
    summary_file = runner.output_dir / f"summary_{runner.session_id}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print(f"\n✅ Summary saved to: {summary_file}")
    print(f"\n📈 Key Results:")

    if "improvements" in summary:
        imp = summary["improvements"]
        print(f"   Time Saved: {imp['time_saved_seconds']:.1f}s ({imp['time_saved_percent']:.1f}%)")
        print(f"   Speedup: {imp['speedup_factor']:.1f}x faster")
        print(f"   Steps Reduced: {imp['steps_reduced']:.1f}")
        print(f"   Files Not Opened: {imp['files_saved']:.0f}")

    print(f"\n   MCP Cost: ${summary['mcp_metrics']['total_cost_usd']:.4f}")
    print(f"   Manual Cost: ${summary['manual_metrics']['total_cost_usd']:.4f}")

    print(f"\n📁 All results: {runner.output_dir}")


if __name__ == "__main__":
    main()
