# Local AI Literature Discovery, Citation-Crawling, and Research Acquisition System

## 1. Objective
Build a local-first research literature discovery system that uses local Ollama models together with external scholarly metadata APIs to discover, rank, crawl, and prioritize academic papers for acquisition and deep analysis.

The system must **NOT** assume that a PDF is available for every paper.

**The core design principle is:**
Use external scholarly services to discover and traverse the scholarly graph; use local AI models to interpret, rank, and guide exploration; acquire PDFs only for high-value candidates; then use the existing local OCR/RAG pipeline for deep analysis.

The system should work starting from a natural-language research question, even when no seed paper is provided. The final product should function as an intelligent research-discovery and paper-acquisition engine rather than merely a PDF search or RAG application.

## 2. Core Architecture
Use a staged pipeline:
1. Research Question
2. Query/Concept Expansion
3. Scholarly Metadata Search
4. Candidate Paper Graph
5. Local AI Ranking
6. Citation / Reference / Recommendation Expansion
7. Iterative Re-ranking
8. High-priority Acquisition Queue
9. PDF Acquisition (through existing university/Paperpile workflow)
10. OCR / Text / Figure / Table Extraction
11. Deep Local AI Analysis
12. Knowledge Graph Enrichment
13. New Concepts/Terminology (Fed back into search and graph expansion)

The system should maintain two distinct graphs:
- **External Scholarly Graph**
- **Local Research Interpretation Graph**

Do not attempt to replace Semantic Scholar/OpenAlex with a locally reconstructed citation database.

## 3. External Scholarly Graph
Use external scholarly APIs as discovery and graph infrastructure.

**Primary sources:**
- Semantic Scholar
- OpenAlex
- Crossref
- Domain-specific databases when appropriate, such as PubMed
- Other scholarly APIs where useful

**Semantic Scholar should be used for:**
- Paper search
- Paper metadata
- Abstracts
- Citations and References
- Authors
- Related/recommended papers
- Citation relationships and recommendation functionality
- Available embeddings/relevance signals where exposed

**OpenAlex should be used for:**
- Broad literature discovery
- Works and Authors
- Institutions
- Topics
- Citation relationships
- Publication metadata
- Research-field/topic structure

Use multiple sources because no single scholarly graph should be considered complete or authoritative. 

**Deduplicate papers primarily using:**
- DOI
- Semantic Scholar paper ID
- OpenAlex work ID
- PMID where applicable
- Normalized title + author/year fallback

Preserve all external identifiers.

## 4. Input: Research Question Instead of Seed Paper
The system must work without a seed paper. The primary input should be a natural-language research question such as: *"Find research investigating whether mechanism X explains phenomenon Y under condition Z."*

A local Ollama model should transform this question into a structured research representation.

**Example:**
- **TARGET:** Phenomenon Y
- **MECHANISM:** X
- **POPULATION:** Z
- **METHODS:** M1, M2, M3
- **ALTERNATIVE TERMINOLOGY:** A, B, C
- **RELATED CONCEPTS:** D, E, F
- **POSSIBLE SYNONYMS:** …
- **EXCLUSIONS:** …
- **TEMPORAL CONSTRAINTS:** …
- **DOMAIN:** …

The query-expansion model should generate multiple independent search formulations rather than one single query.

## 5. Initial Discovery
Search Semantic Scholar and OpenAlex using the expanded query set. **Do not immediately download PDFs.**

The initial discovery stage should produce a candidate set containing metadata such as:
- Title
- Abstract (if available)
- Authors and Affiliations
- Publication Year and Venue
- DOI and Identifiers
- Topics and Keywords
- Citation Count and Reference Count
- Citation relationships
- Open-access information
- Recommendation relationships
- External URLs where available

The initial result might contain hundreds or thousands of candidate papers.

## 6. Metadata-First Relevance Assessment
The local model must **NOT** pretend to know the true relevance of a paper when only metadata is available. Instead, distinguish between:
- Estimated relevance
- Confidence
- Acquisition value
- Novelty potential
- Graph importance
- Uncertainty

The question for the model is: *"Given what is currently known about this paper, is it worth spending additional resources investigating it?"*

Do not use a simple binary relevant/irrelevant classification. Use states such as:
- `DISCARD`
- `LOW_PRIORITY`
- `WATCH`
- `EXPAND`
- `ACQUIRE`
- `UNKNOWN`

`UNKNOWN` should be used when metadata is insufficient to make a reliable decision.

## 7. Metadata-Based Candidate Representation
Represent every paper as a candidate object.

**Example conceptual structure:**
- **Canonical Identifiers:** DOI, Title, Abstract, Authors, Institutions, Year, Venue, Topics, Keywords, Citation count, References, Cited-by relationships, Related papers, Source APIs, Open-access status, PDF availability, Metadata confidence.
- **Local Interpretation:** Research-question match, Methodological match, Population/context match, Conceptual match, Novelty potential, Citation importance, Graph centrality, Bridge potential, Temporal relevance, Discovery source, Local embedding, Local model score, Local model confidence, Reasons for ranking, Decision state.

## 8. Ranking Should Be Relative and Comparative
Do not independently ask an LLM to assign an absolute relevance score to every paper. Instead, periodically give the local model batches of candidates.

**Example:**
- **Research Question:** [research question]
- **Candidate papers:** Paper A, Paper B, Paper C… Paper N

**Ask the model to:**
- Rank candidates by expected research value
- Explain the discriminating features
- Identify misleadingly relevant titles
- Identify papers that appear weak but may be important
- Identify clusters of related candidates
- Identify candidates that should be expanded through their citation graph
- Identify candidates that should be acquired for full-text analysis

Use comparative ranking rather than pretending the model has precise absolute probabilities.

## 9. Priority Queue
The crawler should maintain a dynamic priority queue. The priority should represent: Expected research value / cost of investigating the candidate.

**Potential factors include:**
Metadata relevance, confidence, methodological similarity, conceptual similarity, research-question match, novelty potential, citation importance, graph connectivity, bridge/centrality potential, recency, unexplored branch potential, availability/acquisition cost, uncertainty.

Do not hard-code the final weighting initially. Make the scoring function configurable and log every component so it can later be evaluated against human judgments.

**Example:**
- **Paper A:** Expected value: 0.91 | Confidence: 0.72 | Novelty potential: high | Graph importance: high | Acquisition cost: low | **Decision: ACQUIRE**
- **Paper B:** Expected value: 0.87 | Confidence: 0.48 | Novelty potential: very high | Acquisition cost: unknown | **Decision: EXPAND / WATCH**

The system should prioritize papers that could substantially change the research landscape, not simply papers with the highest semantic similarity.

## 10. Citation Graph Traversal
The system should perform graph traversal in multiple directions.
- **Backward traversal:** Follow references to discover foundational work, earlier methods, original datasets, theoretical origins, and historical development.
- **Forward traversal:** Follow cited-by relationships to discover extensions, replications, newer methods, critiques, and the current state of the field.
- **Lateral traversal:** Explore related papers, same authors, same research groups, same datasets, same methods, same topics, and papers with similar terminology.

Do not restrict the crawler to citation links alone.

## 11. Best-First Search
Treat literature discovery as a graph-search problem. Maintain a frontier of unexplored papers.

**Repeatedly:**
1. Select the highest-value candidate.
2. Inspect its metadata and graph relationships.
3. Discover new candidate papers.
4. Deduplicate them.
5. Rank them.
6. Add promising candidates to the frontier.
7. Repeat.

Do **NOT** use a fixed “crawl three levels deep” rule. The crawler should stop or change direction when marginal discovery value decreases. If a deeper branch produces unusually relevant or novel papers, the system should be able to reopen that branch.

## 12. Scout Role
The Scout is responsible for constructing the initial research landscape. **Scout does NOT require PDFs.**

**Scout should:**
Expand the research question, generate terminology, generate synonyms, generate related concepts, query Semantic Scholar, query OpenAlex, query domain-specific databases, identify candidate authors, identify relevant topics, identify relevant venues, identify promising papers, and identify potentially important citation neighborhoods. 

Scout produces paper identities and metadata, not necessarily PDFs.

## 13. Judge Role
The Judge determines whether a candidate is worth additional investigation. **Judge does NOT require a PDF.**

**Inputs:**
Research objective, candidate title, abstract if available, authors, topics, publication information, citations, relationships to already known papers, recommendation signals.

**Outputs:**
Ranking, confidence, decision, reasoning, missing information, recommended next action.

The Judge should be conservative when metadata is insufficient.

## 14. Cartographer Role
The Cartographer analyzes the structure of the literature graph. **It should not require PDFs.**

**It should identify:**
Citation hubs, foundational papers, highly connected papers, bridge papers, emerging clusters, author/lab clusters, methodological clusters, isolated but semantically relevant papers, temporal transitions, competing schools of thought, research communities, underexplored regions of the graph.

## 15. Synthesizer Role
The Synthesizer periodically evaluates the accumulated research landscape.

**It should answer:**
What themes are emerging? What terminology is emerging? What methods dominate? What methods are declining? What disagreements exist? Which papers appear unusually important? Which branches deserve deeper crawling? What research gaps appear? What concepts are missing from the original query? What new search queries should be generated?

The Synthesizer should be able to modify the next Scout search, creating an iterative discovery loop.

## 16. Active-Learning Loop
The system should learn from accumulated judgments.

**For example:**
- Initial search: 500 candidates
- Local Judge: 50 promising, 100 uncertain, 350 low priority
- After further analysis: 20 PDFs acquired
- Human researcher marks: 15 genuinely useful, 5 not useful

Use these decisions to improve subsequent ranking. Maintain positive and negative examples. Where supported, use external recommendation systems to search for papers similar to positive examples while avoiding patterns associated with rejected examples. The goal is for the system to gradually learn the researcher’s personal definition of: *"This is an interesting paper for my current question."*

## 17. Two-Stage Paper Lifecycle
A paper should progress through explicit states:
`DISCOVERED` → `METADATA_ASSESSED` → `HIGH_PRIORITY` → `ACQUISITION_QUEUE` → `FULL_TEXT_ACQUIRED` → `FULL_TEXT_ANALYZED` → `EVIDENCE_EXTRACTED` → `KNOWLEDGE_GRAPH_ENRICHED`

A PDF is therefore a promotion of an existing metadata object, not the prerequisite for entering the system.

## 18. PDF Acquisition
Do not make the agent responsible for bypassing university authentication or access controls. Use legitimate acquisition paths (open-access copies, institutional access, existing Paperpile workflow, manually retrieved PDFs, publisher/library access, institutional repositories).

**The system should maintain an acquisition queue (HIGH PRIORITY) detailing:**
DOI / title / authors, reason for acquisition, relevance score, confidence, graph importance, and what the paper is expected to contribute.

If automatic acquisition fails, mark `FULL_TEXT_UNAVAILABLE`. The user can retrieve the paper through their normal university/Paperpile workflow. The local system should watch a designated directory for newly acquired PDFs. When a PDF appears, identify DOI/title, match it against the candidate graph, perform OCR/text extraction, analyze the full text, update the research graph, generate new concepts and terminology, and feed those concepts back into discovery.

## 19. Deep PDF Analysis
Only use expensive local processing after a paper has been promoted to the full-text stage. Use existing local OCR/RAG infrastructure.

**Extract:**
Abstract, sections, claims, hypotheses, methods, datasets, experiments, results, limitations, figures, tables, citations, terminology, quantitative findings, evidence, contradictions, methodological relationships. 

The full-text analysis should enrich the existing metadata graph rather than create a disconnected document summary.

## 20. Discovery Feedback Loop
Deep PDF analysis must generate new discovery signals.

**For example, a newly analyzed paper introduces:**
Previously unknown terminology, a new method, an unexpected dataset, an alternative theory, a competing research group, or a new citation cluster. These should be added to the research representation, and new searches should be automatically generated.

**The loop becomes:**
Research Question → Search → Metadata Graph → Ranking → Citation Expansion → PDF Acquisition → Deep Analysis → New Concepts → New Searches → Expanded Graph → Repeat. 
This feedback loop is a central feature, not an optional enhancement.

## 21. Surprise / Novelty Signal
Add a “surprise” signal to candidate prioritization. A paper should receive additional priority if it represents something unexpected relative to the current research model.

**Examples:**
Unexpected method, unexpected dataset, contradictory finding, new terminology, unexpected application of a known method, paper connecting two otherwise separate clusters, highly cited paper with low semantic similarity, new research cluster, paper that challenges an assumption.

The system should not optimize purely for similarity. It should balance:
`RELEVANCE + NOVELTY + GRAPH IMPORTANCE + UNCERTAINTY + EXPECTED INFORMATION VALUE`

## 22. Research Frontier
Maintain a dynamic research-frontier view. The frontier should show:
- **Current research question:** [question]
- **High-value papers:** Papers currently judged most promising.
- **Emerging research threads:** Clusters or themes discovered by the crawler.
- **Important authors/groups:** Authors or institutions repeatedly appearing in promising work.
- **Contradictions:** Papers making conflicting claims.
- **Research gaps:** Areas with evidence of importance but insufficient literature.
- **Unexplored branches:** High-value graph neighborhoods that have not yet been explored.
- **Acquisition queue:** Papers that should be obtained for full-text analysis.
- **Unknowns:** Papers for which metadata is insufficient.

## 23. Provenance and Auditability
Every AI decision must be recorded. For each ranking or classification, store:
Timestamp, model, model version, prompt/version, input metadata, output score, decision, reasoning, evidence used, external data sources, graph relationships considered.

Do not store only: *"relevance = 0.87"*. Instead store: *"relevance = 0.87 because the paper directly addresses the target mechanism, uses the target population, and is connected to three highly ranked papers through citations."* This makes the system auditable and allows later evaluation.

## 24. Local Models
Use a model cascade rather than one model for everything.

**Potential roles:**
- **Small/fast model:** Metadata classification, query expansion, initial ranking, deduplication, simple extraction.
- **Larger local model:** Comparative ranking, conceptual analysis, research landscape interpretation, contradiction detection, research-gap analysis, synthesis.
- **Embedding model:** Semantic similarity, candidate retrieval, clustering, deduplication, novelty detection.

Do not send PDFs to large models until necessary.

## 25. Important Design Principle
The system must distinguish three kinds of knowledge:
- **External facts:** Obtained from scholarly APIs: *"Paper X cites Paper Y."*
- **Metadata inference:** Generated by local models: *"Paper X appears highly relevant to my question."*
- **Full-text evidence:** Extracted from the actual paper: *"Paper X reports result Y under experimental condition Z."*

Never represent these as equivalent. Every piece of information should carry provenance and confidence.

## 26. Initial MVP
Do not build the entire system initially. Build this first:
1. Research Question
2. Local query expansion
3. Semantic Scholar search
4. OpenAlex search
5. Deduplicate
6. Collect metadata
7. Local Ollama comparative ranking
8. Select top 20
9. Expand citations/references/recommendations
10. Deduplicate
11. Re-rank
12. Produce top-30 acquisition queue

Do this **WITHOUT** downloading PDFs. 
Measure how many genuinely useful papers appear in the top 10 and top 30, how many useful papers are discovered through citation expansion that keyword search missed, and how much iterative query expansion improves recall. Only after this works should PDF acquisition and deep analysis be integrated.

## 27. Long-Term Goal
The final system should behave like a persistent local research scout. Given a research question, it should continuously understand the question, expand terminology, search multiple scholarly databases, construct a candidate graph, rank candidates, traverse promising citation neighborhoods, identify emerging research clusters, identify contradictions and gaps, learn the researcher’s preferences, prioritize papers for acquisition, integrate newly acquired PDFs, extract evidence, update the knowledge graph, generate new concepts, and search again.

The system should therefore be viewed as: **a local AI research-discovery and evidence-acquisition engine built on top of external scholarly graphs and a private local knowledge base.**

**The most important architectural principle is:**
`Metadata first. Graph first. PDF second. Deep evidence last.`

Do not require a PDF to discover, rank, or crawl a paper. Use the PDF only when the expected value of obtaining the paper justifies the acquisition and analysis cost.
