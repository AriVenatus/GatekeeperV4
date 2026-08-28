# Skill Observation Log

Observations captured during task-oriented work. Each entry identifies a
potential skill improvement or new skill opportunity.

**Status key:** OPEN = not yet actioned | ACTIONED = skill updated/created |
DECLINED = user decided not to pursue

---

## 2026-08-28

### Observation 1: Prefer already-emitted log lines over restart-gated diagnostics when live access is unavailable
**Status:** OPEN
**Date:** 2026-08-28
**Session context:** Diagnosing why a bot resolved a game server to its fallback module instead of the game-specific one, with no access to the running production system.
**Skill:** ground-truth-debugging
**Type:** open-source
**Phase/Area:** Establishing ground truth when the live system is not directly reachable

**Issue:** The obvious ground-truth signal (the field the detection logic actually compares) was only logged at a custom verbose level that requires a restart flag to enable. The first instinct was to tell the user to restart with that flag. A second pass over the code found several *discriminating* lines already emitted at default INFO/ERROR level — a success line printed only when the game-specific extension loads, and an error line printed only from inside the game-specific class — which together distinguish the competing hypotheses without any restart or config change. The restart-gated line was demoted to a last step, only needed if the cheap checks are inconclusive.

**Suggested improvement:** Add a step to the skill's ground-truth procedure: before recommending any action that changes the system's configuration or restarts it, grep the code for log/telemetry statements that are (a) already emitted at the current level and (b) reachable only on one branch of the hypothesis space. Rank diagnostics by cost: existing artifacts → read-only queries → config change/restart → code change. Explicitly note that a line is only useful as evidence if its *presence or absence* separates hypotheses; a line printed on every path proves nothing.

**Principle:** A diagnostic's value is its discriminating power divided by its cost to obtain. Restart-gated verbose logging is the most expensive tier and is often unnecessary: code paths that only execute under one hypothesis usually already emit something at default level. Search for branch-exclusive log lines before asking anyone to change how the system runs.

### Observation 2: When an API won't reveal a field name, read the vendor's own declarative source instead of guessing again
**Status:** OPEN
**Date:** 2026-08-28
**Session context:** A bot needed one configuration value out of a third-party control panel's HTTP API. Two prior sessions had each shipped a different guess at where that value lived; both were disproven against the live system, and the second guess had shipped to production.
**Skill:** ground-truth-debugging
**Type:** open-source
**Phase/Area:** Fallback research path when the live system is reachable but uninformative

**Issue:** The live system WAS reachable, and the skill's live-inspection path had been followed correctly both times — a probe endpoint was called, its response inspected, and the value wasn't in it. Because live inspection is the skill's top-priority path and it had technically "succeeded", each session concluded with a new hypothesis about a *different* runtime location and shipped it. What neither session did was consult the vendor's published, declarative definition of the object being queried (an open-source template/manifest repository), which stated the field's exact identifier and its full addressing path unambiguously and could be fetched in one request. A single fetch of that file ended a two-session guessing loop.

**Suggested improvement:** Add to the skill: a live probe that comes back *empty or without the thing you're looking for* is a negative result, not ground truth about where the thing lives. Before forming a second hypothesis about a runtime location, check whether the vendor publishes a declarative source of truth for the object — template repos, OpenAPI/JSON schemas, config manifests, migration files, .proto/.thrift definitions, packaged type stubs. Prefer it over any further probing: it names identifiers exactly, is versioned, and is quotable in a code comment so the next reader doesn't re-litigate it. Add a hard stop: after ONE disproven hypothesis about a name or location, switch from probing to reading the definition — never ship a second guess.

**Principle:** "I inspected the live system" is only ground truth for what the system *returned*, never for what it *contains* or how it is addressed. Systems configured from declarative artifacts carry their real vocabulary in those artifacts, and the artifacts are usually public and cheaper to read than the API is to probe. A disproven guess is a signal to change source of evidence, not to guess again in the same source.
