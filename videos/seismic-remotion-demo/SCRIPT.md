# Scene 1

A coding agent can find similar code and still miss the one caller, test or entry point its edit will break. Before the patch lands, it needs proof.

# Scene 2

Meet Seismic. It parses a real Python repository into an immutable Git snapshot inside HydraDB. Every file, function, test and entry point becomes an artifact. Calls, imports and test coverage become directed edges.

# Scene 3

Change bounded int in Seismic itself. The dashboard maps the diff to one symbol, then HydraDB walks reverse dependencies. It finds three impacts: http main, the Seismic HTTP entry point and its transport test. Select the entry point and the exact two-hop path lights up. The agent gets a ready-to-run test and a review decision.

# Scene 4

Ask about a symbol that does not exist and Seismic returns zero. Ask for an unsupported connection and it abstains. Every impact claim has a path or it is not returned.

# Scene 5

The same engine is exposed as eight stateless MCP tools. A coding agent can index a repository, analyze a diff, retrieve context, explain one impact path, record a real incident and inspect durable decision history. State is in HydraDB, so a fresh standard input process and a fresh HTTP client recover the same graph.

# Scene 6

HydraDB is not a log sink. It is Seismic's system of record and path engine. Immutable snapshots and incident identities live in the graph. Native S S paths finds blast radius, M S paths unifies multiple changes and S P paths proves one exact impact. Remove HydraDB and Seismic loses direction, reachability and the evidence behind every gate.

# Scene 7

Working product, not a mock. Twenty-two tests pass: nineteen fast and three live against HydraDB and MCP. Our twelve-case smoke proves ten exact paths and two abstentions. On identical tasks, graph retrieval scores one point zero precision and recall; TF-IDF scores zero point one three two one. Across three real Python repositories, a deterministic target rule returned forty-nine impacts, every path valid. A five-thousand-artifact, twenty-thousand-relationship stress graph recovered twenty-five of twenty-five targets. Seismic gives coding agents an inspectable gate before they edit.
