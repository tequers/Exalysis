"""Build the current taxonomy from independent paper judgments without model calls."""
from copy import deepcopy

from .evaluation import (
    CONTRACT_VERSION, contract_metadata, difficulty_version, summarize_difficulty,
    validate_topic_scores, validate_connection_review,
)


def _has_path(graph, start, goal):
    pending, visited = [start], set()
    while pending:
        node = pending.pop()
        if node == goal:
            return True
        if node not in visited:
            visited.add(node)
            pending.extend(graph.get(node, ()))
    return False


def aggregate_taxonomy(taxonomy, exams):
    """Recompute from a paper-ID snapshot; replacing an ID retracts its old evidence.

    Prior contracts are not silently reinterpreted. Overrides stay on the canonical
    topic; independent paper judgments always store the model's observations.
    """
    result = deepcopy(taxonomy)
    topics = result.setdefault("topics", {})
    samples, edges, excluded = {}, {}, []
    allowed = set(topics)
    for paper in exams.values():
        allowed.update(paper.get("topic_judgments", {}))
    for eid, paper in sorted(exams.items()):
        if paper.get("evaluation_contract_version") != CONTRACT_VERSION or "topic_judgments" not in paper:
            excluded.append(eid)
            continue
        context = paper.get("evaluation_context") or {}
        advisory_quotes = (
            isinstance(context, dict) and context.get("quote_validation") == "advisory")
        judgments = validate_topic_scores(
            paper["topic_judgments"], list(paper["topic_judgments"]),
            paper["questions"], allowed, already_validated=True,
            allow_unverified_quotes=advisory_quotes)
        for name, judgment in judgments.items():
            samples.setdefault(name, {})[eid] = judgment
        review = paper.get("connection_review")
        if review and review.get("evaluation_contract_version") == CONTRACT_VERSION:
            paper_edges = validate_connection_review(review, paper["questions"], allowed)["edges"]
        else:
            paper_edges = [edge for judgment in judgments.values() for edge in judgment["connection_edges"]]
        for edge in paper_edges:
            pair = (edge["prerequisite"], edge["dependent"])
            citation = {"exam_id": eid, **edge}
            evidence = edges.setdefault(pair, [])
            if citation not in evidence:
                evidence.append(citation)

    graph = {}
    for source, target in edges:
        graph.setdefault(source, set()).add(target)
    # Every edge that participates in a cycle needs review; none boosts Conn.
    conflicts = {pair for pair in edges if _has_path(graph, pair[1], pair[0])}
    touched = set(samples) | {node for edge in edges for node in edge}
    touched.update(name for name, topic in topics.items() if topic.get("automatic_summary"))
    for name in sorted(touched):
        previous = topics.get(name, {})
        topic = deepcopy(previous)
        paper_scores = samples.get(name, {})
        outgoing = sorted(target for source, target in edges
                          if source == name and (source, target) not in conflicts)
        incoming = sorted(source for source, target in edges
                          if target == name and (source, target) not in conflicts)
        citations = [citation for pair, evidence in sorted(edges.items())
                     if name in pair for citation in evidence]
        conflict_evidence = [citation for pair in sorted(conflicts)
                             if name in pair for citation in edges[pair]]
        groups = {}
        for eid, judgment in paper_scores.items():
            baseline = tuple(sorted(judgment["assumed_prerequisites"]))
            groups.setdefault(baseline, {})[eid] = [q["level"] for q in judgment["question_difficulty"]]
        summaries = [dict(assumed_prerequisites=list(baseline), exam_ids=sorted(papers),
                          **summarize_difficulty(papers))
                     for baseline, papers in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))]
        if summaries:
            chosen = summaries[0]
            automatic_diff = chosen["Diff"]
            diff_version = CONTRACT_VERSION
            topic.update({k: chosen[k] for k in ("difficulty_range", "difficulty_provisional",
                                                 "assumed_prerequisites")})
            topic["difficulty_review_required"] = len(summaries) > 1 or chosen["difficulty_review_required"]
            topic["difficulty_rationale"] = "Lower median across equally weighted papers with matching background assumptions."
        else:
            automatic_diff = previous.get("model_estimate", {}).get("Diff", previous.get("Diff"))
            diff_version = difficulty_version(previous)
            topic["difficulty_review_required"] = True
            topic["difficulty_provisional"] = True
        automatic_conn = 1 if not outgoing else 2 if len(outgoing) <= 2 else 3
        old_model = previous.get("model_estimate", {})
        overrides = deepcopy(previous.get("human_overrides", {}))
        for field in ("Diff", "Conn"):
            # Once managed, detect direct JSON edits against the last computed value.
            if field not in overrides and field in old_model and previous.get(field) != old_model[field]:
                overrides[field] = {"value": previous[field], "source": "taxonomy.json",
                                    "evaluation_contract_version": (difficulty_version(previous) if field == "Diff"
                                        else previous.get("evaluation_contract_version", "legacy-unversioned"))}
        topic.update(contract_metadata())
        topic.update({
            "automatic_summary": True,
            "model_estimate": {"Diff": automatic_diff, "Conn": automatic_conn},
            "Diff": overrides.get("Diff", {}).get("value", automatic_diff),
            "Conn": overrides.get("Conn", {}).get("value", automatic_conn),
            "difficulty_contract_version": diff_version,
            "difficulty_groups": summaries,
            "unlocks": outgoing, "prerequisites": incoming,
            "connection_evidence": citations,
            "connection_conflicts": conflict_evidence,
            "connection_review_required": bool(conflict_evidence),
            "connection_rationale": f"{len(outgoing)} distinct direct dependent topics supported across stored papers; cyclic links excluded.",
            "contributing_exam_ids": sorted(set(paper_scores) | {c["exam_id"] for c in citations}),
            "excluded_legacy_exam_ids": excluded,
            "human_overrides": overrides,
        })
        topic["connection_provisional"] = len(topic["contributing_exam_ids"]) < 2 or bool(excluded) or bool(conflict_evidence)
        if not topic.get("first_seen"):
            topic["first_seen"] = min(topic["contributing_exam_ids"], default=None)
        # Detailed question judgments stay in their own papers, with unambiguous IDs.
        for key in ("question_difficulty", "prerequisite_evidence", "connection_edges"):
            topic.pop(key, None)
        topics[name] = topic
    return result
