# Local AI Literature Discovery, Citation-Crawling, and Research Acquisition System
Local AI Literature Discovery, Citation-Crawling, and Research Acquisition System

## 1. ObjectiveBuild a local-first research literature discovery system that uses local Ollama models together with external scholarly metadata APIs to discover, rank, crawl, and prioritize academic papers for acquisition and deep analysis.

The system must NOT assume that a PDF is available for every paper.

The core design principle is:
* Use external scholarly services to discover and traverse the scholarly graph; use local AI models to interpret, rank, and guide exploration; acquire PDFs only for high-value candidates; then use the existing local OCR/RAG pipeline for deep analysis.

The system should work starting from a natural-language research question, even when no seed paper is provided.

The final product should function as an intelligent research-discovery and paper-acquisition engine rather than merely a PDF search or RAG application.

## 2. Core ArchitectureUse a staged pipeline:
* Research Question→ Query/Concept Expansion→ Scholarly Metadata Search→ Candidate Paper Graph→ Local AI Ranking→ Citation/Reference/Recommendation Expansion→ Iterative Re-ranking→ High-priority Acquisition Queue→ PDF Acquisition through existing university/Paperpile workflow→ OCR/Text/Figure/Table Extraction→ Deep Local AI Analysis→ Knowledge Graph Enrichment→ New Concepts/Terminology→ Feed discoveries back into search and graph expansionThe system should maintain two distinct graphs:
* External Scholarly GraphLocal Research Interpretation GraphDo not attempt to replace Semantic Scholar/OpenAlex with a locally reconstructed citation database.

## 3. External Scholarly GraphUse external scholarly APIs as discovery and graph infrastructure.

Primary sources:
* Semantic ScholarOpenAlexCrossrefDomain-specific databases when appropriate, such as PubMedOther scholarly APIs where usefulSemantic Scholar should be used for:
* paper searchpaper metadataabstractscitationsreferencesauthorsrelated/recommended paperscitation relationshipsrecommendation functionalityavailable embeddings/relevance signals where exposedOpenAlex should be used for:
* broad literature discoveryworksauthorsinstitutionstopicscitation relationshipspublication metadataresearch-field/topic structureUse multiple sources because no single scholarly graph should be considered complete or authoritative.

Deduplicate papers primarily using:
* DOISemantic Scholar paper IDOpenAlex work IDPMID where applicablenormalized title + author/year fallbackPreserve all external identifiers.

## 4. Input: Research Question Instead of Seed PaperThe system must work without a seed paper.

The primary input should be a natural-language research question such as:“Find research investigating whether mechanism X explains phenomenon Y under condition Z.”A local Ollama model should transform this question into a structured research representation.

Example:
* TARGET:
* phenomenon YMECHANISM:
* XPOPULATION:
* ZMETHODS:
* M1, M2, M3ALTERNATIVE TERMINOLOGY:
* A, B, CRELATED CONCEPTS:
* D, E, FPOSSIBLE SYNONYMS:…EXCLUSIONS:…TEMPORAL CONSTRAINTS:…DOMAIN:…The query-expansion model should generate multiple independent search formulations rather than one query.

## 5. Initial DiscoverySearch Semantic Scholar and OpenAlex using the expanded query set.

Do not immediately download PDFs.

The initial discovery stage should produce a candidate set containing metadata such as:
* titleabstract if availableauthorsaffiliationspublication yearvenueDOIidentifierstopicskeywordscitation countreference countcitation relationshipsopen-access informationrecommendation relationshipsexternal URLs where availableThe initial result might contain hundreds or thousands of candidate papers.

## 6. Metadata-First Relevance AssessmentThe local model must NOT pretend to know the true relevance of a paper when only metadata is available.

Instead, distinguish between:
* estimated relevanceconfidenceacquisition valuenovelty potentialgraph importanceuncertaintyThe question for the model is:“Given what is currently known about this paper, is it worth spending additional resources investigating it?”Do not use a simple binary relevant/irrelevant classification.

Use states such as:
* DISCARDLOW_PRIORITYWATCHEXPANDACQUIREUNKNOWNUNKNOWN should be used when metadata is insufficient to make a reliable decision.

## 7. Metadata-Based Candidate RepresentationRepresent every paper as a candidate object.

Example conceptual structure:
* Paper:
* canonical identifierDOItitleabstractauthorsinstitutionsyearvenuetopicskeywordscitation countreferencescited-by relationshipsrelated papersrecommendation relationshipssource APIsopen-access statusPDF availabilitymetadata confidenceLocal interpretation:
* research-question matchmethodological matchpopulation/context matchconceptual matchnovelty potentialcitation importancegraph centralitybridge potentialtemporal relevancediscovery sourcelocal embeddinglocal model scorelocal model confidencereasons for rankingdecision state

## 8. Ranking Should Be Relative and ComparativeDo not independently ask an LLM to assign an absolute relevance score to every paper.

Instead, periodically give the local model batches of candidates.

Example:
* Research Question:[research question]Candidate papers:
* Paper APaper BPaper C…Paper NAsk the model to:
* rank candidates by expected research valueexplain the discriminating featuresidentify misleadingly relevant titlesidentify papers that appear weak but may be importantidentify clusters of related candidatesidentify candidates that should be expanded through their citation graphidentify candidates that should be acquired for full-text analysisUse comparative ranking rather than pretending the model has precise absolute probabilities.

## 9. Priority QueueThe crawler should maintain a dynamic priority queue.

The priority should represent:
* Expected research value / cost of investigating the candidatePotential factors include:
* metadata relevanceconfidencemethodological similarityconceptual similarityresearch-question matchnovelty potentialcitation importancegraph connectivitybridge/centrality potentialrecencyunexplored branch potentialavailability/acquisition costuncertaintyDo not hard-code the final weighting initially.

Make the scoring function configurable and log every component so it can later be evaluated against human judgments.

Example:
* Paper A:
* Expected value: 0.91Confidence: 0.72Novelty potential: highGraph importance: highAcquisition cost: lowDecision:
* ACQUIREPaper B:
* Expected value: 0.87Confidence: 0.48Novelty potential: very highAcquisition cost: unknownDecision:
* EXPAND / WATCHThe system should prioritize papers that could substantially change the research landscape, not simply papers with the highest semantic similarity.

## 10. Citation Graph TraversalThe system should perform graph traversal in multiple directions.

Backward traversalFollow references to discover:
* foundational workearlier methodsoriginal datasetstheoretical originshistorical developmentForward traversalFollow cited-by relationships to discover:
* extensionsreplicationsnewer methodscritiquescurrent state of the fieldLateral traversalExplore:
* related paperssame authorssame research groupssame datasetssame methodssame topicspapers with similar terminologyDo not restrict the crawler to citation links alone.

## 11. Best-First SearchTreat literature discovery as a graph-search problem.

Maintain a frontier of unexplored papers.

Repeatedly:
* select the highest-value candidateinspect its metadata and graph relationshipsdiscover new candidate papersdeduplicate themrank themadd promising candidates to the frontierrepeatDo NOT use a fixed “crawl three levels deep” rule.

The crawler should stop or change direction when marginal discovery value decreases.

If a deeper branch produces unusually relevant or novel papers, the system should be able to reopen that branch.

## 12. Scout RoleThe Scout is responsible for constructing the initial research landscape.

Scout does NOT require PDFs.

Scout should:
* expand the research questiongenerate terminologygenerate synonymsgenerate related conceptsquery Semantic Scholarquery OpenAlexquery domain-specific databasesidentify candidate authorsidentify relevant topicsidentify relevant venuesidentify promising papersidentify potentially important citation neighborhoodsScout produces paper identities and metadata, not necessarily PDFs.

## 13. Judge RoleThe Judge determines whether a candidate is worth additional investigation.

Judge does NOT require a PDF.Inputs:
* research objectivecandidate titleabstract if availableauthorstopicspublication informationcitationsrelationships to already known papersrecommendation signalsOutputs:
* rankingconfidencedecisionreasoningmissing informationrecommended next actionPossible decisions:
* DISCARDWATCHEXPANDACQUIREUNKNOWNThe Judge should be conservative when metadata is insufficient.

## 14. Cartographer RoleThe Cartographer analyzes the structure of the literature graph.

It should identify:
* citation hubsfoundational papershighly connected papersbridge papersemerging clustersauthor/lab clustersmethodological clustersisolated but semantically relevant paperstemporal transitionscompeting schools of thoughtresearch communitiesunderexplored regions of the graphThe Cartographer should work primarily with metadata and graph structure.

It should not require PDFs.

## 15. Synthesizer RoleThe Synthesizer periodically evaluates the accumulated research landscape.

It should answer:
* What themes are emerging?What terminology is emerging?What methods dominate?What methods are declining?What disagreements exist?Which papers appear unusually important?Which branches deserve deeper crawling?What research gaps appear?What concepts are missing from the original query?What new search queries should be generated?The Synthesizer should be able to modify the next Scout search.

This creates an iterative discovery loop.

## 16. Active-Learning LoopThe system should learn from accumulated judgments.

For example:
* Initial search:500 candidatesLocal Judge:50 promising100 uncertain350 low priorityAfter further analysis:20 PDFs acquiredHuman researcher marks:15 genuinely useful5 not usefulUse these decisions to improve subsequent ranking.

Maintain positive and negative examples.

Where supported, use external recommendation systems such as Semantic Scholar’s recommendation functionality to search for papers similar to positive examples while avoiding patterns associated with rejected examples.

The goal is for the system to gradually learn the researcher’s personal definition of:“This is an interesting paper for my current question.”

## 17. Two-Stage Paper LifecycleA paper should progress through explicit states:
* DISCOVERED→ METADATA_ASSESSED→ HIGH_PRIORITY→ ACQUISITION_QUEUE→ FULL_TEXT_ACQUIRED→ FULL_TEXT_ANALYZED→ EVIDENCE_EXTRACTED→ KNOWLEDGE_GRAPH_ENRICHEDA PDF is therefore a promotion of an existing metadata object, not the prerequisite for entering the system.

## 18. PD

F AcquisitionDo not make the agent responsible for bypassing university authentication or access controls.

Use legitimate acquisition paths:
* open-access copiesinstitutional accessexisting Paperpile workflowmanually retrieved PDFspublisher/library accessinstitutional repositoriesThe system should maintain an acquisition queue such as:
* HIGH PRIORITY:
* DOI / title / authorsreason for acquisitionrelevance scoreconfidencegraph importancewhat the paper is expected to contributeIf automatic acquisition fails, mark:
* FULL_TEXT_UNAVAILABLEThe user can retrieve the paper through their normal university/Paperpile workflow.

The local system should watch a designated directory for newly acquired PDFs.

When a PDF appears:
* identify DOI/titlematch it against the candidate graphassociate it with the candidateperform OCR/text extractionanalyze the full textupdate the research graphgenerate new concepts and terminologyfeed those concepts back into discovery

## 19. Deep PDF AnalysisOnly use expensive local processing after a paper has been promoted to the full-text stage.

Use existing local OCR/RAG infrastructure.

Extract:
* abstractsectionsclaimshypothesesmethodsdatasetsexperimentsresultslimitationsfigurestablescitationsterminologyquantitative findingsevidencecontradictionsmethodological relationshipsThe full-text analysis should enrich the existing metadata graph rather than create a disconnected document summary.

## 20. Discovery Feedback LoopDeep PDF analysis must generate new discovery signals.

For example:
* A newly analyzed paper introduces:
* previously unknown terminologya new methodan unexpected datasetan alternative theorya competing research groupa new citation clusterThese should be added to the research representation.

Then automatically generate new searches.

The loop becomes:
* Research Question→ Search→ Metadata Graph→ Ranking→ Citation Expansion→ PDF Acquisition→ Deep Analysis→ New Concepts→ New Searches→ Expanded Graph→ RepeatThis feedback loop is a central feature, not an optional enhancement.

## 21. Surprise / Novelty SignalAdd a “surprise” signal to candidate prioritization.

A paper should receive additional priority if it represents something unexpected relative to the current research model.

Examples:
* unexpected methodunexpected datasetcontradictory findingnew terminologyunexpected application of a known methodpaper connecting two otherwise separate clustershighly cited paper with low semantic similaritynew research clusterpaper that challenges an assumptionThe system should not optimize purely for similarity.

It should balance:
* RELEVANCE+NOVELTY+GRAPH IMPORTANCE+UNCERTAINTY+EXPECTED INFORMATION VALUE

## 22. Research FrontierMaintain a dynamic research-frontier view.

The frontier should show:
* Current research question[question]High-value papersPapers currently judged most promising.

Emerging research threadsClusters or themes discovered by the crawler.

Important authors/groupsAuthors or institutions repeatedly appearing in promising work.

ContradictionsPapers making conflicting claims.

Research gapsAreas with evidence of importance but insufficient literature.

Unexplored branchesHigh-value graph neighborhoods that have not yet been explored.

Acquisition queuePapers that should be obtained for full-text analysis.

UnknownsPapers for which metadata is insufficient.

## 23. Provenance and AuditabilityEvery AI decision must be recorded.

For each ranking or classification, store:
* timestampmodelmodel versionprompt/versioninput metadataoutput scoredecisionreasoningevidence usedexternal data sourcesgraph relationships consideredDo not store only:“relevance = 0.87”Instead store:“relevance = 0.87 because the paper directly addresses the target mechanism, uses the target population, and is connected to three highly ranked papers through citations.”This makes the system auditable and allows later evaluation.

## 24. Local ModelsUse a model cascade rather than one model for everything.

Potential roles:
* Small/fast model:
* metadata classificationquery expansioninitial rankingdeduplicationsimple extractionLarger local model:
* comparative rankingconceptual analysisresearch landscape interpretationcontradiction detectionresearch-gap analysissynthesisEmbedding model:
* semantic similaritycandidate retrievalclusteringdeduplicationnovelty detectionDo not send PDFs to large models until necessary.

## 25. Important Design PrincipleThe system must distinguish three kinds of knowledge:
* External factsObtained from scholarly APIs:“Paper X cites Paper Y.”Metadata inferenceGenerated by local models:“Paper X appears highly relevant to my question.”Full-text evidenceExtracted from the actual paper:“Paper X reports result Y under experimental condition Z.”Never represent these as equivalent.

Every piece of information should carry provenance and confidence.

## 26. Initial MVPDo not build the entire system initially.

Build this first:
* Research Question→ local query expansion→ Semantic Scholar search→ OpenAlex search→ deduplicate→ collect metadata→ local Ollama comparative ranking→ select top 20→ expand citations/references/recommendations→ deduplicate→ re-rank→ produce top-30 acquisition queueDo this WITHOUT downloading PDFs.

Measure:
* How many genuinely useful papers appear in the top 10?How many appear in the top 30?How many useful papers are discovered through citation expansion that keyword search missed?How often does the local model incorrectly prioritize a paper?How often does graph traversal find important papers with mediocre semantic similarity?Which external API contributes the most useful discoveries?How much does iterative query expansion improve recall?Only after this works should PDF acquisition and deep analysis be integrated.

## 27. Long-Term GoalThe final system should behave like a persistent local research scout.

Given a research question, it should continuously:
* understand the questionexpand terminologysearch multiple scholarly databasesconstruct a candidate graphrank candidatestraverse promising citation neighborhoodsidentify emerging research clustersidentify contradictions and gapslearn the researcher’s preferencesprioritize papers for acquisitionintegrate newly acquired PDFsextract evidenceupdate the knowledge graphgenerate new conceptssearch againThe system should therefore be viewed as:
* a local AI research-discovery and evidence-acquisition engine built on top of external scholarly graphs and a private local knowledge base.

The most important architectural principle is:
* Metadata first. Graph first. PDF second. Deep evidence last.

Do not require a PDF to discover, rank, or crawl a paper.

Use the PDF only when the expected value of obtaining the paper justifies the acquisition and analysis cost.