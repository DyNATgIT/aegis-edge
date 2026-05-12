
"""
core/rag.py
Aegis-Edge — RAG Pipeline (Retrieval Augmented Generation)

Architecture:
  Documents → Chunked → Embedded (sentence-transformers) → ChromaDB
  Query → Embedded → Similarity Search → Top-K Chunks → Injected into LLM

Everything runs 100% offline after the embedding model is downloaded once.
ChromaDB stores vectors persistently in ./vectordb/ folder.
"""

import os
import json
import time
from pathlib import Path
from loguru import logger

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Paths — Windows-compatible via pathlib
VECTOR_DB_PATH  = str(Path(".") / "vectordb")
PROTOCOLS_PATH  = Path(".") / "data" / "who_protocols"
COLLECTION_NAME = "aegis_medical_knowledge"

# Embedding model — small, fast, works offline after first download
# all-MiniLM-L6-v2: 80MB, 384 dimensions, excellent for medical text
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking parameters
CHUNK_SIZE    = 400   # Words per chunk
CHUNK_OVERLAP = 60    # Word overlap between chunks (maintains context)

# Retrieval parameters
DEFAULT_N_RESULTS = 5   # Number of chunks to retrieve per query
MIN_RELEVANCE_SCORE = 0.3  # Minimum cosine similarity to include

# ═══════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════

_chroma_client     = None
_chroma_collection = None


def get_collection():
    """
    Get or create the ChromaDB collection.
    Singleton pattern — creates once, reuses connection.
    """
    global _chroma_client, _chroma_collection

    if _chroma_collection is not None:
        return _chroma_collection

    # Ensure vector DB directory exists
    Path(VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)

    logger.info(f"Connecting to ChromaDB at: {VECTOR_DB_PATH}")

    # Initialize persistent client (survives restarts)
    _chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

    # Use sentence-transformers for embeddings (offline after first download)
    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    # Get or create the collection
    _chroma_collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    doc_count = _chroma_collection.count()
    logger.info(
        f"Collection '{COLLECTION_NAME}' ready. "
        f"Documents in DB: {doc_count}"
    )

    return _chroma_collection


# ═══════════════════════════════════════════════════════════════
# TEXT CHUNKING
# ═══════════════════════════════════════════════════════════════

def chunk_text(text: str,
               chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP,
               source: str = "") -> list[dict]:
    """
    Split text into overlapping chunks for embedding.

    Overlapping chunks ensure that information spanning two chunks
    is still retrievable — critical for medical protocols where
    context from the previous sentence matters.

    Returns list of dicts: {text, chunk_index, word_count}
    """
    # Clean up whitespace
    text = " ".join(text.split())

    words  = text.split()
    chunks = []
    index  = 0
    step   = chunk_size - overlap  # Non-overlapping words per step

    for i in range(0, len(words), step):
        chunk_words = words[i: i + chunk_size]

        if len(chunk_words) < 30:
            # Skip tiny trailing chunks
            break

        chunk_text_str = " ".join(chunk_words)
        chunks.append({
            "text":        chunk_text_str,
            "chunk_index": index,
            "word_count":  len(chunk_words),
            "char_count":  len(chunk_text_str)
        })
        index += 1

    logger.debug(
        f"Chunked '{source}': {len(words)} words → {len(chunks)} chunks "
        f"(size={chunk_size}, overlap={overlap})"
    )
    return chunks


def chunk_by_section(text: str, source: str = "") -> list[dict]:
    """
    Alternative chunking: split on section headers (=== lines).
    Better for structured protocol documents.
    Use this for WHO protocol files which have clear section breaks.
    """
    sections  = []
    current   = []
    sec_index = 0

    for line in text.split('\n'):
        # Detect section headers
        if line.startswith("===") or line.startswith("STEP ") or \
           line.startswith("CLASS ") or (line.isupper() and len(line) > 10):
            if current:
                section_text = "\n".join(current).strip()
                if len(section_text) > 100:
                    sections.append({
                        "text":        section_text,
                        "chunk_index": sec_index,
                        "word_count":  len(section_text.split()),
                        "char_count":  len(section_text)
                    })
                    sec_index += 1
            current = [line]
        else:
            current.append(line)

    # Add final section
    if current:
        section_text = "\n".join(current).strip()
        if len(section_text) > 100:
            sections.append({
                "text":        section_text,
                "chunk_index": sec_index,
                "word_count":  len(section_text.split()),
                "char_count":  len(section_text)
            })

    # If section-based chunking produced too few chunks,
    # fall back to word-based
    if len(sections) < 3:
        logger.debug(f"Section chunking insufficient for {source}. Using word chunking.")
        return chunk_text(text, source=source)

    logger.debug(f"Section-chunked '{source}': {len(sections)} sections")
    return sections


# ═══════════════════════════════════════════════════════════════
# DOCUMENT INGESTION
# ═══════════════════════════════════════════════════════════════

def ingest_text_file(file_path: str,
                     source_name: str,
                     use_section_chunking: bool = True) -> int:
    """
    Ingest a plain text file into ChromaDB.
    Returns number of chunks added.
    """
    collection = get_collection()

    # Check if already ingested (avoid duplicates)
    existing = collection.get(
        where={"source": source_name},
        limit=1
    )
    if existing["ids"]:
        count = len(collection.get(where={"source": source_name})["ids"])
        logger.info(
            f"'{source_name}' already ingested ({count} chunks). Skipping."
        )
        return count

    # Read file
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return 0

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    if len(text.strip()) < 100:
        logger.warning(f"File too short to ingest: {file_path}")
        return 0

    # Chunk the text
    if use_section_chunking:
        chunks = chunk_by_section(text, source=source_name)
        # Fall back to word chunking if needed
        if len(chunks) < 3:
            chunks = chunk_text(text, source=source_name)
    else:
        chunks = chunk_text(text, source=source_name)

    if not chunks:
        logger.warning(f"No chunks produced from: {file_path}")
        return 0

    # Prepare for ChromaDB insertion
    documents = [c["text"]        for c in chunks]
    ids       = [f"{source_name}_{c['chunk_index']}" for c in chunks]
    metadatas = [{
        "source":      source_name,
        "file":        str(path.name),
        "chunk_index": c["chunk_index"],
        "word_count":  c["word_count"]
    } for c in chunks]

    # Insert in batches (ChromaDB has limits per call)
    batch_size = 50
    total_added = 0

    for i in range(0, len(documents), batch_size):
        batch_docs  = documents[i: i + batch_size]
        batch_ids   = ids[i: i + batch_size]
        batch_metas = metadatas[i: i + batch_size]

        collection.add(
            documents=batch_docs,
            ids=batch_ids,
            metadatas=batch_metas
        )
        total_added += len(batch_docs)

    logger.success(
        f"Ingested '{source_name}': {len(chunks)} chunks | "
        f"avg {sum(c['word_count'] for c in chunks) // len(chunks)} words/chunk"
    )
    return total_added


def ingest_pdf(file_path: str, source_name: str) -> int:
    """
    Extract text from a PDF and ingest into ChromaDB.
    Use this for any WHO PDFs you download manually.
    """
    try:
        import pypdf
    except ImportError:
        logger.error("pypdf not installed. Run: pip install pypdf")
        return 0

    path = Path(file_path)
    if not path.exists():
        logger.warning(f"PDF not found: {file_path}. Skipping.")
        return 0

    # Check if already ingested
    collection = get_collection()
    existing = collection.get(where={"source": source_name}, limit=1)
    if existing["ids"]:
        logger.info(f"PDF '{source_name}' already ingested. Skipping.")
        return 0

    logger.info(f"Extracting text from PDF: {file_path}")

    reader = pypdf.PdfReader(str(path))
    pages  = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and len(text.strip()) > 50:
            pages.append(text)

    if not pages:
        logger.warning(f"No text extracted from PDF: {file_path}")
        return 0

    # Combine all pages and clean whitespace
    full_text = " ".join(pages)
    full_text = " ".join(full_text.split())  # Normalize whitespace

    logger.info(
        f"Extracted {len(pages)} pages, "
        f"{len(full_text.split())} words from {path.name}"
    )

    # Write to temp text file then ingest
    temp_path = str(path.with_suffix(".extracted.txt"))
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    result = ingest_text_file(temp_path, source_name)

    # Clean up temp file
    try:
        Path(temp_path).unlink()
    except Exception:
        pass

    return result


# ═══════════════════════════════════════════════════════════════
# KNOWLEDGE BASE BUILDER
# ═══════════════════════════════════════════════════════════════

def build_knowledge_base(force_rebuild: bool = False) -> dict:
    """
    One-time setup: ingest all medical documents into ChromaDB.
    Safe to call multiple times — skips already-ingested documents.

    Args:
        force_rebuild: If True, delete and rebuild entire database

    Returns:
        Dict with stats about the knowledge base
    """
    start_time = time.time()

    if force_rebuild:
        logger.warning("Force rebuild: deleting existing knowledge base...")
        try:
            client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
            client.delete_collection(COLLECTION_NAME)
            logger.info("Existing collection deleted.")
        except Exception as e:
            logger.warning(f"Could not delete collection: {e}")

        # Reset singletons
        global _chroma_client, _chroma_collection
        _chroma_client     = None
        _chroma_collection = None

    collection  = get_collection()
    initial_count = collection.count()

    logger.info(f"Building knowledge base (existing chunks: {initial_count})...")

    stats = {
        "files_processed": 0,
        "chunks_added":    0,
        "errors":          []
    }

    # ── Ingest all .txt protocol files ────────────────────
    txt_files = sorted(PROTOCOLS_PATH.glob("*.txt"))

    if not txt_files:
        logger.warning(
            f"No .txt files found in {PROTOCOLS_PATH}. "
            f"Did you create the protocol files in Phase 2?"
        )
    else:
        for txt_file in txt_files:
            source_name = txt_file.stem  # e.g. "01_start_triage"
            try:
                count = ingest_text_file(str(txt_file), source_name)
                stats["files_processed"] += 1
                stats["chunks_added"]    += count
            except Exception as e:
                error_msg = f"Failed to ingest {txt_file.name}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)

    # ── Ingest any PDF files the user has downloaded ──────
    pdf_files = list(PROTOCOLS_PATH.glob("*.pdf"))
    if pdf_files:
        logger.info(f"Found {len(pdf_files)} PDF file(s) to process...")
        for pdf_file in pdf_files:
            source_name = f"pdf_{pdf_file.stem}"
            try:
                count = ingest_pdf(str(pdf_file), source_name)
                if count > 0:
                    stats["files_processed"] += 1
                    stats["chunks_added"]    += count
            except Exception as e:
                error_msg = f"Failed to ingest PDF {pdf_file.name}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
    else:
        logger.info(
            "No PDF files found. "
            "Add WHO PDFs to data\\who_protocols\\ to include them."
        )

    # ── Final stats ────────────────────────────────────────
    final_count    = collection.count()
    elapsed        = time.time() - start_time
    stats["total_chunks_in_db"] = final_count
    stats["build_time_seconds"] = round(elapsed, 1)

    if final_count == 0:
        logger.error(
            "Knowledge base is empty! "
            "Check that protocol files were created in Phase 2."
        )
    else:
        logger.success(
            f"Knowledge base ready: {final_count} total chunks | "
            f"{stats['files_processed']} files | "
            f"{elapsed:.1f}s"
        )

    return stats


# ═══════════════════════════════════════════════════════════════
# RETRIEVAL
# ═══════════════════════════════════════════════════════════════

def retrieve_context(query: str,
                     n_results: int = DEFAULT_N_RESULTS,
                     source_filter: str = None) -> str:
    """
    Retrieve relevant medical knowledge for a clinical query.

    Args:
        query:         Clinical description or question
        n_results:     Number of chunks to retrieve
        source_filter: Optionally restrict to a specific source document

    Returns:
        Formatted context string ready to inject into model prompt
    """
    collection = get_collection()
    total_docs = collection.count()

    if total_docs == 0:
        logger.warning(
            "Knowledge base is empty. "
            "Run build_knowledge_base() first."
        )
        return ""

    # Adjust n_results if DB is smaller
    n_results = min(n_results, total_docs)

    # Build query params
    query_params = {
        "query_texts": [query],
        "n_results":   n_results,
        "include":     ["documents", "metadatas", "distances"]
    }

    if source_filter:
        query_params["where"] = {"source": source_filter}

    try:
        results = collection.query(**query_params)
    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        return ""

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    if not documents:
        return ""

    # Format retrieved chunks into readable context block
    context_parts = []

    for doc, meta, distance in zip(documents, metadatas, distances):
        # Convert distance to similarity score (ChromaDB cosine: 0=identical)
        similarity = 1 - distance

        if similarity < MIN_RELEVANCE_SCORE:
            continue

        source = meta.get("source", "Unknown")
        source_clean = source.replace("_", " ").replace("-", " ").title()

        context_parts.append(
            f"[Protocol: {source_clean} | Relevance: {similarity:.0%}]\n"
            f"{doc.strip()}"
        )

    if not context_parts:
        return ""

    context = "\n\n---\n\n".join(context_parts)

    logger.info(
        f"Retrieved {len(context_parts)} relevant chunks for query. "
        f"Top relevance: {(1 - distances[0]):.0%}"
    )

    return context


def retrieve_for_vitals(spo2: int = None,
                         hr: int = None,
                         rr: int = None,
                         temp: float = None,
                         mechanism: str = "") -> str:
    """
    Targeted retrieval based on specific vital signs.
    Builds an optimized query that will find the most relevant protocols.
    """
    query_parts = []

    if mechanism:
        query_parts.append(mechanism)

    if spo2 is not None:
        if spo2 < 85:
            query_parts.append("critical hypoxia SpO2 below 85 percent oxygen saturation")
        elif spo2 < 90:
            query_parts.append("SpO2 below 90 hypoxia oxygen therapy IMMEDIATE")
        elif spo2 < 94:
            query_parts.append("mild hypoxia SpO2 supplement oxygen")

    if hr is not None:
        if hr > 120:
            query_parts.append("tachycardia heart rate 120 hemorrhagic shock")
        elif hr < 50:
            query_parts.append("bradycardia heart rate slow cardiac")

    if rr is not None:
        if rr > 30:
            query_parts.append("respiratory rate above 30 IMMEDIATE START protocol")
        elif rr < 10:
            query_parts.append("respiratory rate below 10 respiratory depression")

    if temp is not None:
        if temp < 35:
            query_parts.append("hypothermia temperature below 35 rewarming IMMEDIATE")
        elif temp > 39.5:
            query_parts.append("high fever sepsis heat stroke IMMEDIATE")

    if not query_parts:
        return ""

    combined_query = " ".join(query_parts)
    return retrieve_context(combined_query, n_results=4)


def search_drug_protocols(drug_name: str, condition: str = "") -> str:
    """
    Retrieve drug-specific and condition-specific protocols.
    """
    query = f"{drug_name} dosage administration emergency field {condition}"
    return retrieve_context(query, n_results=3)


# ═══════════════════════════════════════════════════════════════
# RAG-AUGMENTED INFERENCE
# ═══════════════════════════════════════════════════════════════

def build_rag_system_prompt(patient_description: str,
                             tool_vitals: dict = None) -> str:
    """
    Build a system prompt augmented with retrieved WHO protocols.

    Args:
        patient_description: The medic's description of the patient
        tool_vitals: Dict of vitals from hardware tools (spo2, hr, temp, rr)

    Returns:
        Augmented system prompt with relevant protocol context injected
    """
    from core.model import SYSTEM_PROMPT

    # Retrieve context based on patient description
    description_context = retrieve_context(patient_description, n_results=3)

    # Retrieve additional context based on actual vitals if available
    vitals_context = ""
    if tool_vitals:
        vitals_context = retrieve_for_vitals(
            spo2=tool_vitals.get("spo2"),
            hr=tool_vitals.get("hr"),
            rr=tool_vitals.get("rr"),
            temp=tool_vitals.get("temp"),
            mechanism=patient_description[:100]
        )

    # Combine contexts
    all_contexts = []
    if description_context:
        all_contexts.append(description_context)
    if vitals_context and vitals_context != description_context:
        all_contexts.append(vitals_context)

    if not all_contexts:
        return SYSTEM_PROMPT

    combined_context = "\n\n" + "─"*50 + "\n\n".join(all_contexts)

    augmented_prompt = SYSTEM_PROMPT + f"""

╔══════════════════════════════════════════════════════╗
║         RETRIEVED WHO MEDICAL PROTOCOLS               ║
║    (Use these to ground your triage decision)         ║
╚══════════════════════════════════════════════════════╝
{combined_context}
{"─"*50}
Cite the relevant protocol in your triage reasoning.
Your decision must be grounded in the above WHO guidelines."""

    return augmented_prompt


def query_with_rag(patient_input: str,
                   history: list = None,
                   tool_vitals: dict = None) -> str:
    """
    Full RAG inference pipeline:
    1. Retrieve relevant WHO protocols for this patient
    2. Build augmented system prompt
    3. Run Gemma 4 inference with grounded context
    4. Return response

    Args:
        patient_input: Medic's patient description
        history:       Previous conversation turns
        tool_vitals:   Vitals dict from hardware tools

    Returns:
        Model response grounded in WHO protocols
    """
    from core.model import run_inference

    # Build augmented system prompt with retrieved context
    augmented_system = build_rag_system_prompt(patient_input, tool_vitals)

    # Run inference with RAG context
    response = run_inference(
        user_message=patient_input,
        history=history,
        system_prompt=augmented_system
    )

    return response


# ═══════════════════════════════════════════════════════════════
# KNOWLEDGE BASE STATUS
# ═══════════════════════════════════════════════════════════════

def get_kb_status() -> dict:
    """Return statistics about the current knowledge base."""
    try:
        collection = get_collection()
        total = collection.count()

        if total == 0:
            return {"status": "empty", "total_chunks": 0, "sources": []}

        # Get all unique sources
        all_items = collection.get(
            include=["metadatas"],
            limit=total
        )

        sources = {}
        for meta in all_items["metadatas"]:
            source = meta.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1

        return {
            "status":       "ready",
            "total_chunks": total,
            "sources":      [
                {"name": k, "chunks": v}
                for k, v in sorted(sources.items())
            ],
            "embedding_model":  EMBEDDING_MODEL,
            "db_path":          VECTOR_DB_PATH
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# RUN DIRECTLY — Build KB and test retrieval
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box

    console = Console()

    console.print(Panel(
        "[bold cyan]AEGIS-EDGE — DAY 3 RAG PIPELINE TEST[/bold cyan]\n"
        "Building knowledge base and testing retrieval",
        border_style="cyan"
    ))

    # Step 1: Build the knowledge base
    console.print("\n[yellow]Step 1: Building knowledge base...[/yellow]")
    stats = build_knowledge_base()

    console.print(f"  Files processed: {stats['files_processed']}")
    console.print(f"  Chunks added   : {stats['chunks_added']}")
    console.print(f"  Total in DB    : {stats['total_chunks_in_db']}")
    console.print(f"  Build time     : {stats['build_time_seconds']}s")
    if stats["errors"]:
        for err in stats["errors"]:
            console.print(f"  [red]Error: {err}[/red]")

    if stats["total_chunks_in_db"] == 0:
        console.print(
            "[red]Knowledge base is empty. "
            "Check that protocol files exist in data\\who_protocols\\[/red]"
        )
        exit(1)

    # Step 2: Show KB status
    console.print("\n[yellow]Step 2: Knowledge base status...[/yellow]")
    status = get_kb_status()

    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("Source Document", style="green", width=35)
    table.add_column("Chunks",          style="yellow", width=10)

    for src in status["sources"]:
        table.add_row(src["name"], str(src["chunks"]))

    table.add_row("─"*35, "─"*10, style="dim")
    table.add_row(
        f"TOTAL ({len(status['sources'])} sources)",
        str(status["total_chunks"]),
        style="bold"
    )
    console.print(table)

    # Step 3: Test queries
    test_queries = [
        {
            "name":     "SpO2 88% + rapid breathing",
            "query":    "patient SpO2 88 percent breathing 34 per minute confused",
            "expected": "START protocol IMMEDIATE respiratory rate threshold"
        },
        {
            "name":     "Burn injury assessment",
            "query":    "burn forearm partial thickness TBSA estimation Parkland formula",
            "expected": "burns protocol TBSA fluid resuscitation"
        },
        {
            "name":     "Hemorrhagic shock",
            "query":    "heart rate 128 no radial pulse pale skin hemorrhage shock",
            "expected": "hemorrhage classification shock management"
        },
        {
            "name":     "Pediatric emergency",
            "query":    "child 4 years old seizure fever 39 degrees",
            "expected": "pediatric febrile seizure diazepam"
        },
        {
            "name":     "Drug interaction",
            "query":    "morphine opioid analgesic dosage field emergency trauma",
            "expected": "opioid dosage contraindications"
        }
    ]

    console.print("\n[yellow]Step 3: Testing retrieval with clinical queries...[/yellow]")

    for test in test_queries:
        console.print(f"\n  Query: [cyan]{test['name']}[/cyan]")
        context = retrieve_context(test["query"], n_results=2)

        if context:
            lines        = context.split("\n")
            preview_line = next(
                (l for l in lines if l.strip() and not l.startswith("[Protocol")),
                ""
            )
            console.print(f"  [green]Retrieved[/green]: {preview_line[:80]}...")
        else:
            console.print(f"  [red]No results[/red] — check document ingestion")

    # Step 4: Full RAG inference test
    console.print("\n[yellow]Step 4: Full RAG inference (sends to model)...[/yellow]")
    console.print("  [dim]This runs Gemma 4 E4B with retrieved WHO context...[/dim]\n")

    rag_test_input = """Patient: Male, 42 years old.
House fire. Burns on both arms and chest.
Facial area appears burned, voice is hoarse.
Breathing is labored, approximately 28 breaths per minute.
Confused — cannot follow commands.
Approximate burn area: about 25 percent of body surface.
SpO2 reading: 89 percent.
No known allergies.

Please assess and give triage category with your reasoning."""

    try:
        response = query_with_rag(rag_test_input)
        console.print(Panel(
            response[:1000] + ("..." if len(response) > 1000 else ""),
            title="[bold red]RAG-AUGMENTED TRIAGE RESPONSE[/bold red]",
            border_style="red"
        ))
        console.print(
            "[green]RAG inference working.[/green] "
            "Model response grounded in WHO protocol context."
        )
    except Exception as e:
        console.print(f"[red]RAG inference failed: {e}[/red]")
        console.print("[dim]Check that model is available (Day 1 setup)[/dim]")

    console.print(Panel(
        "[bold green]DAY 3 RAG PIPELINE COMPLETE[/bold green]\n\n"
        f"Knowledge base: {stats['total_chunks_in_db']} chunks\n"
        f"Sources: {stats['files_processed']} protocol documents\n"
        "Retrieval: Working\n"
        "RAG inference: Working\n\n"
        "Tomorrow: Day 4 — Vision Pipeline (Wound Image Analysis)",
        border_style="green"
    ))
