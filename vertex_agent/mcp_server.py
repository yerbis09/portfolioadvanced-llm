"""
mcp_server.py — MCP wrapper for the vertex_agent package.

Exposes the GCP documentation assistant as stdio tools so Copilot,
Claude, and other MCP clients can ask questions, search chunks, and
queue new documents for ingestion.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import anyio
from mcp import types
from mcp.server import InitializationOptions, Server
from mcp.server.stdio import stdio_server

from vertex_agent.agent import Agent
from vertex_agent.ingester import Ingester
from vertex_agent.retriever import Retriever

_SERVER_NAME = "portfolioadvanced-llm"
_SERVER_VERSION = "0.1.0"

_TOOLS = (
    types.Tool(
        name="ask_gcp",
        description="Answer a question about GCP using the Vertex AI RAG agent.",
        inputSchema={
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
            "additionalProperties": False,
        },
    ),
    types.Tool(
        name="search_gcp_docs",
        description="Search the BigQuery-backed knowledge base for relevant chunks.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    ),
    types.Tool(
        name="ingest_gcp_doc",
        description="Validate and store a document payload via Pub/Sub -> BigQuery.",
        inputSchema={
            "type": "object",
            "properties": {
                "payload": {
                    "type": "object",
                    "additionalProperties": True,
                }
            },
            "required": ["payload"],
            "additionalProperties": False,
        },
    ),
)


def ask_question(question: str, agent: Agent | None = None) -> str:
    """Answer *question* using the RAG agent."""
    active_agent = agent or Agent()
    return active_agent.ask(question)


def search_documentation(
    query: str,
    top_k: int = 5,
    retriever: Retriever | None = None,
) -> list[dict[str, str]]:
    """Return the top-k matching knowledge chunks as plain dictionaries."""
    active_retriever = retriever or Retriever()
    chunks = active_retriever.search(query, top_k=top_k)
    return [
        {
            "doc_id": chunk.doc_id,
            "chunk_text": chunk.chunk_text,
            "source_url": chunk.source_url,
        }
        for chunk in chunks
    ]


def ingest_document(
    payload: Mapping[str, Any],
    ingester: Ingester | None = None,
) -> dict[str, Any]:
    """Validate and store a document payload via Pub/Sub -> BigQuery."""
    active_ingester = ingester or Ingester()
    chunks = active_ingester.ingest_direct(dict(payload))
    return {
        "status": "ok",
        "chunk_count": len(chunks),
        "doc_id": chunks[0].doc_id if chunks else "unknown",
    }


async def _list_tools() -> types.ListToolsResult:
    return types.ListToolsResult(tools=list(_TOOLS))


async def _call_tool(params: types.CallToolRequestParams) -> types.CallToolResult:
    name = params.name
    arguments = params.arguments or {}

    if name == "ask_gcp":
        result = ask_question(str(arguments["question"]))
    elif name == "search_gcp_docs":
        result = search_documentation(
            str(arguments["query"]),
            top_k=int(arguments.get("top_k", 5)),
        )
    elif name == "ingest_gcp_doc":
        result = ingest_document(arguments["payload"])
    else:
        return types.CallToolResult(
            isError=True,
            content=[types.TextContent(text=f"Unknown tool: {name}")],
        )

    return types.CallToolResult(
        content=[types.TextContent(text=json.dumps(result, ensure_ascii=True, indent=2))],
    )


async def _run_server() -> None:
    server = Server(
        _SERVER_NAME,
        version=_SERVER_VERSION,
        title="portfolioadvanced-llm MCP server",
        description="GCP documentation assistant exposed as MCP tools.",
        on_list_tools=lambda _ctx, _params=None: _list_tools(),
        on_call_tool=lambda _ctx, params: _call_tool(params),
    )
    init_options = InitializationOptions(
        server_name=_SERVER_NAME,
        server_version=_SERVER_VERSION,
        title="portfolioadvanced-llm MCP server",
        description="GCP documentation assistant exposed as MCP tools.",
        capabilities=types.ServerCapabilities(tools=types.ToolsCapability(listChanged=False)),
    )
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


def main() -> None:
    """Run the MCP server over stdio."""
    anyio.run(_run_server)


if __name__ == "__main__":
    main()
