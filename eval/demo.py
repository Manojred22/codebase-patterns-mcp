#!/usr/bin/env python3
"""
Before/After Demo for LinkedIn open-source launch.

Three scenes:
  Scene 1 (static): Claude WITHOUT MCP — generic Jaeger/localhost output
  Scene 2 (LIVE):   Actual MCP search results for telemetry query
  Scene 3 (static): Claude WITH MCP — uses AcmeTracerConfig with compliance fields

Usage:
    python eval/demo.py
"""

import json
import os
import sys
from pathlib import Path
from textwrap import dedent

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()


# --- Scene 1: Claude WITHOUT MCP (pre-recorded) ---

SCENE_1_GENERIC_OUTPUT = dedent("""\
    // Claude's output WITHOUT the MCP codebase search:

    package main

    import (
        "go.opentelemetry.io/otel"
        "go.opentelemetry.io/otel/exporters/jaeger"
        sdktrace "go.opentelemetry.io/otel/sdk/trace"
    )

    func initTracer() (*sdktrace.TracerProvider, error) {
        exporter, err := jaeger.New(jaeger.WithCollectorEndpoint(
            jaeger.WithEndpoint("http://localhost:14268/api/traces"),
        ))
        if err != nil {
            return nil, err
        }

        tp := sdktrace.NewTracerProvider(
            sdktrace.WithBatcher(exporter),
        )
        otel.SetTracerProvider(tp)
        return tp, nil
    }
""")

# --- Scene 3: Claude WITH MCP (pre-recorded) ---

SCENE_3_ACME_OUTPUT = dedent("""\
    // Claude's output WITH the MCP codebase search — uses the team's actual pattern:

    package main

    import (
        "log"
        "myservice/pkg/telemetry"
    )

    func main() {
        tp, err := telemetry.NewTracer(telemetry.AcmeTracerConfig{
            ServiceName: "order-service",
            TeamLabel:   "payments",          // Required for compliance
            CostCenter:  "CC-2847",           // Required for billing
            Environment: "production",
            SampleRate:  0.1,                 // Acme default: 10%
        })
        if err != nil {
            log.Fatalf("Failed to init tracer: %v", err)
        }
        defer telemetry.Shutdown(context.Background())

        // ... rest of service setup
    }
""")


def print_divider(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def run_demo():
    """Run the three-scene demo."""

    # --- Scene 1 ---
    print_divider("SCENE 1: Claude WITHOUT MCP (generic output)")
    print("Prompt: 'Add telemetry tracing to my Go service'\n")
    print(SCENE_1_GENERIC_OUTPUT)
    print("Problems:")
    print("  - Uses Jaeger exporter (team uses OTLP/gRPC)")
    print("  - Points to localhost (team has telemetry.internal.acme.com)")
    print("  - Missing TeamLabel, CostCenter compliance fields")
    print("  - No sampling configuration")

    # --- Scene 2: LIVE search ---
    print_divider("SCENE 2: LIVE MCP Search Results")
    print("Prompt: 'Add telemetry tracing to my Go service'")
    print("Tool called: search_code(query='add telemetry tracing to a Go service')\n")

    try:
        from src.vector_store import VectorStore
        from src.embeddings import EmbeddingGenerator

        chroma_path = os.getenv("CHROMA_PATH", "./data/chroma_db")
        embedding_generator = EmbeddingGenerator()
        vector_store = VectorStore(
            persist_directory=chroma_path,
            embedding_generator=embedding_generator,
        )

        results = vector_store.search(
            "add telemetry tracing to a Go service",
            n_results=5,
            filter_metadata={"language": "go"},
        )

        if not results:
            print("[No results — have you indexed the sample repos?]")
            print("Run: python index_repos.py --reset")
        else:
            print(f"Found {len(results)} results:\n")
            for i, r in enumerate(results, 1):
                meta = r["metadata"]
                score = 1.0 - r.get("distance", 0.0)
                print(f"  Result {i}: {r['id']}")
                print(f"  Repo: {meta.get('repo')} | File: {meta.get('file')}")
                print(f"  Patterns: {meta.get('patterns')} | Frameworks: {meta.get('frameworks')}")
                print(f"  Relevance: {score:.2%}")
                print(f"  Source code:")
                for line in r["content"].split("\n")[:15]:
                    print(f"    {line}")
                if len(r["content"].split("\n")) > 15:
                    print(f"    ... ({len(r['content'].split(chr(10)))} total lines)")
                print()

    except Exception as e:
        print(f"[Live search failed: {e}]")
        print("This is expected if the vector store isn't populated yet.")
        print("Run: cp -r sample-repos/* repos/ && python index_repos.py --reset")

    # --- Scene 3 ---
    print_divider("SCENE 3: Claude WITH MCP (uses team patterns)")
    print("Same prompt: 'Add telemetry tracing to my Go service'\n")
    print(SCENE_3_ACME_OUTPUT)
    print("Improvements:")
    print("  + Uses team's telemetry.NewTracer() factory")
    print("  + Includes AcmeTracerConfig with all required fields")
    print("  + TeamLabel + CostCenter for compliance/billing")
    print("  + Connects to telemetry.internal.acme.com (not localhost)")
    print("  + Proper sampling rate (Acme default 10%)")
    print("  + Graceful shutdown with defer")

    print_divider("CONCLUSION")
    print("Same prompt, completely different output.")
    print("The MCP server gives Claude access to your team's actual patterns,")
    print("so generated code follows your internal standards from day one.")


if __name__ == "__main__":
    run_demo()
