# Cypher Write Reference

This reference covers everything needed to write correct WRITE queries
from the ArchivistOutput contract. You will write MERGE, SET, and
relationship creation statements. Never write DELETE or REMOVE.

---

## Core principle — MERGE not CREATE

Always use MERGE instead of CREATE for both nodes and relationships.
MERGE is idempotent — safe to retry if the pipeline fails mid-run.
CREATE on a node that already exists creates a duplicate. Never use it.

---

## Node — create

MERGE on the name property within the label set.
ON CREATE SET populates all properties on first write.
ON MATCH SET only updates aliases — handles the case where MERGE
finds an existing node on a retry.

```cypher
MERGE (n:Person:ConditionalTemporal {{name: $name}})
ON CREATE SET
  n.aliases         = $aliases,
  n.sourceUrls      = $sourceUrls,
  n.confidence      = $confidence,
  n.createdAt       = datetime(),
  n.validFrom       = $validFrom,
  n.extra_nationality = $nationality,
  n.extra_birthDate   = $birthDate
ON MATCH SET
  n.aliases    = apoc.coll.union(n.aliases, $aliases),
  n.sourceUrls = apoc.coll.union(n.sourceUrls, $sourceUrls);
```

Flatten all `extra` dict keys onto the node with `extra_` prefix.
Never store `extra` as a raw map property — map properties are not indexable.

Example mapping from contract to query params:

```
contract extra: {{ "orgType": "commercial_bank", "sector": "finance" }}
params:   {{ "orgType": "commercial_bank", "sector": "finance" }}
cypher:   n.extra_orgType = $orgType, n.extra_sector = $sector
```

For nodes with no extra properties, omit the extra_ lines entirely.

---

## Node — update

Match strictly by elementId. Never match by name for an update.
Only SET the properties specified in the contract.
Never overwrite createdAt or confidence on update.

```cypher
MATCH (n)
WHERE elementId(n) = $resolvedId
SET
  n.aliases    = apoc.coll.union(n.aliases, $newAliases),
  n.sourceUrls = apoc.coll.union(n.sourceUrls, $newSourceUrls);
```

If validUntil is being set (supersession only — never otherwise):

```cypher
MATCH (n)
WHERE elementId(n) = $resolvedId
SET
  n.validUntil = $validUntil,
  n.sourceUrls = apoc.coll.union(n.sourceUrls, $newSourceUrls);
```

---

## Relationship — create

Match both endpoint nodes by elementId before creating the relationship.
MERGE on the full relationship pattern — safe to retry.
Flatten extra dict properties with extra_ prefix, same as nodes.

```cypher
MATCH (a) WHERE elementId(a) = $fromNodeId
MATCH (b) WHERE elementId(b) = $toNodeId
MERGE (a)-[r:RELATIONSHIP_TYPE]->(b)
ON CREATE SET
  r.context     = $context,
  r.sourceUrls  = $sourceUrls,
  r.validFrom   = $validFrom,
  r.validUntil  = null,
  r.confidence  = $confidence,
  r.extra_title = $title,
  r.extra_appointingBody = $appointingBody
ON MATCH SET
  r.sourceUrls = apoc.coll.union(r.sourceUrls, $sourceUrls);
```

Replace `RELATIONSHIP_TYPE` with the exact type from the contract —
e.g. `HOLDS_POSITION`, `OWNS_STAKE`, `PARTICIPATED_IN`.

---

## Relationship — update_urls

Only appends a new sourceUrl to an active (non-closed) relationship.
Match by elementId for both nodes plus the relationship type.
Filter WHERE validUntil IS NULL to target only the active instance.

```cypher
MATCH (a) WHERE elementId(a) = $fromNodeId
MATCH (b) WHERE elementId(b) = $toNodeId
MATCH (a)-[r:RELATIONSHIP_TYPE]->(b)
WHERE r.validUntil IS NULL
SET r.sourceUrls = apoc.coll.union(r.sourceUrls, $newSourceUrls);
```

Nothing else is updated. Do not touch context, confidence, or validFrom.

---

## Relationship — supersession (closing an old relationship)

Only generated when the contract includes a relationship being explicitly
superseded by a new one. Two queries are always generated together:
one to close the old, one to create the new.

Query 1 — close the old relationship:

```cypher
MATCH (a) WHERE elementId(a) = $fromNodeId
MATCH (b) WHERE elementId(b) = $toNodeId
MATCH (a)-[r:RELATIONSHIP_TYPE]->(b)
WHERE r.validUntil IS NULL
SET
  r.validUntil = $validUntil,
  r.sourceUrls = apoc.coll.union(r.sourceUrls, $supersessionSourceUrls);
```

Query 2 — create the new relationship:
Use the standard relationship create pattern above.

The old and new relationship are separate instances. Both will exist in the
graph — old one closed, new one open. This is the correct historical record.

---

## apoc.coll.union

Used to merge two lists without duplicates. Required for aliases and sourceUrls.

```cypher
apoc.coll.union(n.aliases, $newAliases)
```

Returns a list containing all elements from both lists, deduplicated.
Requires APOC plugin. Confirm availability on your Neo4j instance before use.

If APOC is unavailable, handle list merging in Python before query execution
and pass the final merged list as a single param.

---

## Parameterisation rules

All values go in params. Never interpolate strings into Cypher.

Rejected:
```cypher
MERGE (n:Person {{name: "Kwame Mensah"}})
```

Accepted:
```cypher
MERGE (n:Person {{name: $name}})
-- params: {{ "name": "Kwame Mensah" }}
```

Null values must be passed explicitly in params:

```cypher
ON CREATE SET n.validFrom = $validFrom
-- params: {{ "validFrom": null }}
```

Do not omit null params — the query must be complete and self-contained.

---

## Output format

Return a JSON array. One object per query.

[
  {{
    "operation": "node_create",
    "cypher": "MERGE (n:Organisation:ConditionalTemporal {{name: $name}}) ON CREATE SET ...",
    "params": {{
      "name": "Savanna Microfinance Bank",
      "aliases": ["SMB"],
      "sourceUrls": ["https://example-news.com/article-1"],
      "confidence": 0.91,
      "validFrom": null,
      "orgType": "microfinance_bank",
      "sector": "financial_services"
    }}
  }},
  {{
    "operation": "relationship_create",
    "cypher": "MATCH (a) WHERE elementId(a) = $fromNodeId MATCH (b) WHERE elementId(b) = $toNodeId MERGE (a)-[r:OWNS_STAKE]->(b) ON CREATE SET ...",
    "params": {{
      "fromNodeId": "4:abc123:1",
      "toNodeId": "4:def456:2",
      "context": "Meridian Capital Group acquired a 34% equity stake in Savanna Microfinance Bank in October 2024 as part of a recapitalisation exercise mandated by the central bank.",
      "sourceUrls": ["https://example-news.com/article-1"],
      "validFrom": "2024-10-01",
      "confidence": 0.89,
      "percentage": 34.0,
      "acquisitionDate": "2024-10-01",
      "acquisitionPrice": null,
      "currency": null
    }}
  }},
  {{
    "operation": "relationship_update_urls",
    "cypher": "MATCH (a) WHERE elementId(a) = $fromNodeId MATCH (b) WHERE elementId(b) = $toNodeId MATCH (a)-[r:EMPLOYED_BY]->(b) WHERE r.validUntil IS NULL SET r.sourceUrls = apoc.coll.union(r.sourceUrls, $newSourceUrls);",
    "params": {{
      "fromNodeId": "4:ghi789:3",
      "toNodeId": "4:jkl012:4",
      "newSourceUrls": ["https://example-news.com/article-1"]
    }}
  }}
]

Valid operation values:
- `node_create`
- `node_update`
- `relationship_create`
- `relationship_update_urls`
- `relationship_supersede_close`
- `relationship_supersede_create`

---

## Hard Rules

1. Never use CREATE — always MERGE
2. Never DELETE or REMOVE anything
3. Never interpolate values — always parameterise
4. Never match a node by name for an update — always elementId()
5. Never set validUntil unless the contract explicitly provides it
6. Never overwrite createdAt or confidence on a node update
7. Never merge unrelated operations into one query
8. Always filter WHERE r.validUntil IS NULL when updating an active relationship
9. Supersession always generates exactly two queries — close then create