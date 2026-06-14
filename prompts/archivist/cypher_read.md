# Cypher Read Reference

This reference covers everything you need to write correct READ queries
against the knowledge graph. You will only ever write MATCH statements —
never CREATE, MERGE, SET, or DELETE.

---

## Basic MATCH

Find a node by a single property:

```cypher
MATCH (n:Person {name: "Kwame Mensah"})
RETURN n
```

Find a node by label only:

```cypher
MATCH (n:Organisation)
RETURN n.name, n.extra_sector
```

---

## WHERE clause

Use WHERE for conditions that are not simple equality:

```cypher
MATCH (n:Person)
WHERE n.name = "Kwame Mensah"
RETURN n
```

Multiple conditions:

```cypher
MATCH (n:Organisation)
WHERE n.extra_sector = "financial_services"
AND n.extra_orgType = "commercial_bank"
RETURN n
```

Check for null:

```cypher
MATCH (n:Person)
WHERE n.validUntil IS NULL
RETURN n
```

Check list membership:

```cypher
MATCH (n)
WHERE "KCCA" IN n.aliases
RETURN n
```

---

## Matching by elementId

Always use elementId() when you have a resolved node ID.
Never match by name alone for updates — names are not unique identifiers.

```cypher
MATCH (n)
WHERE elementId(n) = "4:abc123:0"
RETURN n
```

Match two nodes by their IDs:

```cypher
MATCH (a), (b)
WHERE elementId(a) = "4:abc123:0"
AND elementId(b) = "4:def456:1"
RETURN a, b
```

---

## Fuzzy name matching

Use `apoc.text.sorensenDiceSimilarity` for fuzzy search.
Only consider results above 0.85 similarity.

```cypher
MATCH (n)
WHERE apoc.text.sorensenDiceSimilarity(
  toLower(n.name), toLower($searchName)
) > 0.85
RETURN n, apoc.text.sorensenDiceSimilarity(
  toLower(n.name), toLower($searchName)
) AS score
ORDER BY score DESC
LIMIT 5
```

Search across both name and aliases:

```cypher
MATCH (n)
WHERE apoc.text.sorensenDiceSimilarity(toLower(n.name), toLower($searchName)) > 0.85
OR any(alias IN n.aliases WHERE
  apoc.text.sorensenDiceSimilarity(toLower(alias), toLower($searchName)) > 0.85
)
RETURN n
LIMIT 5
```

---

## Matching relationships

Check if a relationship exists between two resolved nodes:

```cypher
MATCH (a)-[r:HOLDS_POSITION]->(b)
WHERE elementId(a) = "4:abc123:0"
AND elementId(b) = "4:def456:1"
RETURN r
```

Check if an active (non-closed) relationship exists:

```cypher
MATCH (a)-[r:HOLDS_POSITION]->(b)
WHERE elementId(a) = "4:abc123:0"
AND elementId(b) = "4:def456:1"
AND r.validUntil IS NULL
RETURN r
```

Check if any relationship of any type exists between two nodes:

```cypher
MATCH (a)-[r]->(b)
WHERE elementId(a) = "4:abc123:0"
AND elementId(b) = "4:def456:1"
RETURN type(r), r
```

---

## Checking existing labels and relationship types

Get all labels currently in the graph:

```cypher
CALL db.labels() YIELD label
RETURN label
ORDER BY label
```

Get all relationship types currently in the graph:

```cypher
CALL db.relationshipTypes() YIELD relationshipType
RETURN relationshipType
ORDER BY relationshipType
```

---

## Returning specific properties

Return selected properties rather than the full node:

```cypher
MATCH (n:Organisation {name: "Meridian Bank"})
RETURN
  elementId(n) AS id,
  n.name AS name,
  n.aliases AS aliases,
  n.extra_orgType AS orgType,
  n.extra_sector AS sector
```

---

## Search strategy for entity resolution

When resolving an entity from an article, run searches in this order.
Stop at the first match. Do not run all searches if an earlier one succeeds.

**Step 1 — Exact name match**

```cypher
MATCH (n {name: $exactName})
RETURN elementId(n) AS id, labels(n) AS labels, n.name AS name, n.aliases AS aliases
LIMIT 1
```

**Step 2 — Alias match**

```cypher
MATCH (n)
WHERE $searchName IN n.aliases
RETURN elementId(n) AS id, labels(n) AS labels, n.name AS name, n.aliases AS aliases
LIMIT 1
```

**Step 3 — Fuzzy match (only if steps 1 and 2 returned nothing)**

```cypher
MATCH (n)
WHERE apoc.text.sorensenDiceSimilarity(toLower(n.name), toLower($searchName)) > 0.85
OR any(alias IN n.aliases WHERE
  apoc.text.sorensenDiceSimilarity(toLower(alias), toLower($searchName)) > 0.85
)
RETURN
  elementId(n) AS id,
  labels(n) AS labels,
  n.name AS name,
  n.aliases AS aliases,
  apoc.text.sorensenDiceSimilarity(toLower(n.name), toLower($searchName)) AS score
ORDER BY score DESC
LIMIT 3
```

A fuzzy match result must be flagged with `suggestedMerge: true`.
Never treat a fuzzy match as a confirmed exact match.

---

## Hard Rules

1. Never write CREATE, MERGE, SET, DELETE, or REMOVE
2. Always use parameterised queries — values in `$params`, never interpolated
3. Always use `elementId()` for node lookups by ID — never use internal integer IDs
4. Limit all fuzzy searches to prevent runaway scans — always include `LIMIT`
5. When checking for an active relationship, always filter `WHERE r.validUntil IS NULL`