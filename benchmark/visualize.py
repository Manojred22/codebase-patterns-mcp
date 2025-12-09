#!/usr/bin/env python3
"""
Visualize benchmark results with charts and tables
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


def load_summary(summary_file: str) -> Dict:
    """Load benchmark summary"""
    with open(summary_file) as f:
        return json.load(f)


def print_comparison_table(summary: Dict):
    """Print comparison table"""
    print("\n" + "="*80)
    print("📊 MCP vs MANUAL - COMPARISON TABLE")
    print("="*80)

    mcp = summary["mcp_metrics"]
    manual = summary["manual_metrics"]

    # Table header
    print(f"\n{'Metric':<30} {'MCP (Mean)':<20} {'Manual (Mean)':<20} {'Improvement'}")
    print("-"*80)

    # Time metrics
    print(f"{'Search Time (s)':<30} {mcp['search_time']['mean']:>18.2f}  {manual['search_time']['mean']:>18.2f}  ", end="")
    time_improvement = (manual['search_time']['mean'] - mcp['search_time']['mean']) / manual['search_time']['mean'] * 100
    print(f"{time_improvement:>5.1f}% faster")

    print(f"{'Total Time (s)':<30} {mcp['total_time']['mean']:>18.2f}  {manual['total_time']['mean']:>18.2f}  ", end="")
    total_improvement = (manual['total_time']['mean'] - mcp['total_time']['mean']) / manual['total_time']['mean'] * 100
    print(f"{total_improvement:>5.1f}% faster")

    # Quality metrics
    print(f"{'Results Found':<30} {mcp['results_found']['mean']:>18.1f}  {manual['results_found']['mean']:>18.1f}  ", end="")
    results_diff = mcp['results_found']['mean'] - manual['results_found']['mean']
    print(f"{results_diff:>+6.1f} results")

    # User experience metrics
    print(f"{'Manual Steps':<30} {mcp['manual_steps']['mean']:>18.1f}  {manual['manual_steps']['mean']:>18.1f}  ", end="")
    steps_saved = manual['manual_steps']['mean'] - mcp['manual_steps']['mean']
    print(f"{steps_saved:>6.1f} fewer")

    print(f"{'Files Opened':<30} {mcp['files_opened']['mean']:>18.1f}  {manual['files_opened']['mean']:>18.1f}  ", end="")
    files_saved = manual['files_opened']['mean'] - mcp['files_opened']['mean']
    print(f"{files_saved:>6.1f} fewer")

    # Cost metrics
    print(f"{'Total Cost ($)':<30} ${mcp['total_cost_usd']:>17.4f}  ${manual['total_cost_usd']:>17.4f}  ", end="")
    cost_diff = mcp['total_cost_usd'] - manual['total_cost_usd']
    print(f"${cost_diff:>+6.4f}")


def print_summary_stats(summary: Dict):
    """Print key summary statistics"""
    if "improvements" not in summary:
        print("\n⚠️  Not enough data for improvement calculations")
        return

    imp = summary["improvements"]

    print("\n" + "="*80)
    print("🎯 KEY IMPROVEMENTS")
    print("="*80)

    print(f"\n⏱️  Time Savings:")
    print(f"   • {imp['time_saved_seconds']:.1f} seconds saved per query")
    print(f"   • {imp['time_saved_percent']:.1f}% faster")
    print(f"   • {imp['speedup_factor']:.1f}x speedup")

    print(f"\n👤 User Experience:")
    print(f"   • {imp['steps_reduced']:.1f} fewer manual steps")
    print(f"   • {imp['files_saved']:.0f} fewer files to open manually")

    print(f"\n💰 Cost Analysis:")
    print(f"   • MCP: ${summary['mcp_metrics']['total_cost_usd']:.4f}")
    print(f"   • Manual: ${summary['manual_metrics']['total_cost_usd']:.4f} (developer time)")
    print(f"   • Net: Very cost effective")

    # Extrapolate to daily usage
    queries_per_day = 10
    print(f"\n📈 Extrapolated (assuming {queries_per_day} queries/day):")
    print(f"   • Time saved per day: {imp['time_saved_seconds'] * queries_per_day / 60:.1f} minutes")
    print(f"   • Time saved per week: {imp['time_saved_seconds'] * queries_per_day * 5 / 3600:.1f} hours")
    print(f"   • Monthly MCP cost: ${summary['mcp_metrics']['total_cost_usd'] * queries_per_day * 20:.2f}")


def print_test_details(summary: Dict):
    """Print detailed test information"""
    print("\n" + "="*80)
    print("📋 TEST DETAILS")
    print("="*80)

    print(f"\nTotal Tests Run: {summary['total_tests']}")
    print(f"   MCP Tests: {summary['mcp_tests']}")
    print(f"   Manual Tests: {summary['manual_tests']}")
    print(f"Generated: {summary['generated_at']}")


def generate_ascii_chart(mcp_time: float, manual_time: float):
    """Generate ASCII bar chart"""
    print("\n" + "="*80)
    print("📊 TIME COMPARISON (ASCII Chart)")
    print("="*80)

    max_time = max(mcp_time, manual_time)
    scale = 50 / max_time  # Scale to 50 chars max

    mcp_bar = "█" * int(mcp_time * scale)
    manual_bar = "█" * int(manual_time * scale)

    print(f"\nMCP     │{mcp_bar} {mcp_time:.2f}s")
    print(f"Manual  │{manual_bar} {manual_time:.2f}s")
    print(f"\nSpeedup: {manual_time / mcp_time:.1f}x faster with MCP")


def main():
    """Main visualization function"""
    if len(sys.argv) < 2:
        # Find latest summary
        results_dir = Path("./benchmark/results")
        summaries = list(results_dir.glob("summary_*.json"))
        if not summaries:
            print("❌ No benchmark results found. Run benchmark.py first.")
            return 1
        summary_file = max(summaries, key=lambda p: p.stat().st_mtime)
        print(f"📁 Using latest results: {summary_file}")
    else:
        summary_file = sys.argv[1]

    summary = load_summary(summary_file)

    print("\n" + "="*80)
    print("🏁 MCP BENCHMARK RESULTS")
    print("="*80)

    print_test_details(summary)
    print_comparison_table(summary)
    print_summary_stats(summary)

    if "improvements" in summary:
        mcp_time = summary["mcp_metrics"]["total_time"]["mean"]
        manual_time = summary["manual_metrics"]["total_time"]["mean"]
        generate_ascii_chart(mcp_time, manual_time)

    print("\n" + "="*80)
    print("✅ Analysis Complete!")
    print("="*80)


if __name__ == "__main__":
    sys.exit(main())
