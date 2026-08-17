# Scene 1

A coding agent can find similar code and still miss the one caller, test or entry point its edit will break. Before the patch lands, it needs proof.

# Scene 2

Meet Seismic. It parses a real Python repository into an immutable Git snapshot inside HydraDB. Every file, function, test and entry point becomes an artifact. Calls, imports and test coverage become directed edges.

# Scene 3

Change calculate. Seismic asks HydraDB to walk reverse dependency paths, not guess from nearby text. In this snapshot it finds five affected artifacts, including the service handler. Select it and the exact path lights up: calculate, total, handler. Two hops, two calls and no hidden reasoning.

# Scene 4

Ask about a symbol that does not exist and Seismic returns zero. Ask for an unsupported connection and it abstains. Every impact claim has a path or it is not returned.

# Scene 5

The same engine is exposed as stateless MCP tools. A coding agent can index a repository, analyze a diff, retrieve context, explain one impact path and record a real incident. Durable state is in HydraDB, so a fresh standard input process and a fresh HTTP client recover the same graph.

# Scene 6

Incident evidence attaches to stable identities across snapshots. Future rankings can weigh exact historical breakage without rewriting old commits. Native S S paths answers one change, M S paths analyzes multiple targets and S P paths proves one source-to-target claim.

# Scene 7

This is working, not a mock. Sixteen tests: thirteen fast and three live against local HydraDB and real MCP transports. Our twelve-case smoke passes ten exact paths and two abstentions. A five-thousand-artifact, twenty-thousand-relationship stress run recovered the right target twenty-five out of twenty-five times. Seismic gives coding agents a blast radius they can inspect before they edit.
