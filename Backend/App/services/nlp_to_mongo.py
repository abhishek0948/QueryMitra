"""
nlp_to_mongo.py
Convert plain-English prompts into MongoDB queries/aggregation pipelines.

✦ How it works (high level)
1) Provide a schema so the parser knows field names and types.
2) Call nlp_to_mongo(prompt, schema, collection="myCol").
3) It returns either:
   - {"type": "find", "query": {...}, "projection": {...}, "sort": [...], "limit": N}
   - {"type": "aggregate", "pipeline": [ ... ]}

The parser is lightweight (regex + keyword cues) but handles:
- Filters: =, !=, >, <, ≥, ≤, BETWEEN, IN, contains, starts with
- Dates: today, yesterday, last N days/weeks/months/years, before/after YYYY-MM-DD
- Aggregations: count, sum, avg/average, min, max, distinct count
- Grouping: group by / per / by
- Sorting & limits: sort by, top N, bottom N, highest/lowest
- Projections: show/list <fields>

You can extend the VOCAB and PATTERNS near the top.

Example:
schema = {
    "amount": "number",
    "category": "string",
    "created_at": "date",
    "status": "string",
    "user_id": "string"
}
prompt = "average amount by category for last 30 days where status = completed, top 5"
print(nlp_to_mongo(prompt, schema))
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

# --------------------------
# Helpers & configuration
# --------------------------

_NUM = r"(?:-?\d+(?:\.\d+)?)"
_DATE_ISO = r"\d{4}-\d{2}-\d{2}"
_QUOTED = r"'([^']*)'|\"([^\"]*)\""

AGG_WORDS = {
    "count": ["count", "how many", "number of", "total rows"],
    "sum": ["sum", "total", "add up"],
    "avg": ["avg", "average", "mean"],
    "min": ["min", "minimum", "lowest"],
    "max": ["max", "maximum", "highest"],
    "distinct": ["distinct", "unique"]
}

COMPARE_SYNONYMS = {
    ">=": ["at least", "greater than or equal to", "gte", "≥"],
    "<=": ["at most", "less than or equal to", "lte", "≤"],
    ">": ["greater than", "more than", "over", "above", ">", "after"],  # "after" used only for dates
    "<": ["less than", "fewer than", "under", "below", "<", "before"],   # "before" used only for dates
    "!=": ["not equal", "not equals", "!="],
    "=": ["equal", "equals", "=", "is", "are"]
}

LOGICAL_JOINERS = ["and", "&&", "&", ",", "as well as", "with"]

CONTAINS_SYNONYMS = ["contains", "include", "includes", "having", "has"]
STARTS_WITH_SYNONYMS = ["starts with", "begin with", "begins with", "prefix"]
ENDS_WITH_SYNONYMS = ["ends with", "suffix"]

GROUP_BY_SYNONYMS = ["group by", "by", "per"]
SORT_SYNONYMS = ["sort by", "order by"]
DESC_WORDS = ["desc", "descending", "highest", "top", "largest", "newest", "latest", "most"]
ASC_WORDS = ["asc", "ascending", "lowest", "bottom", "smallest", "oldest", "earliest", "least"]

PROJECTION_WORDS = ["show", "list", "display", "select"]

# --------------------------
# Date parsing (lightweight)
# --------------------------

def _now() -> datetime:
    # If you want to pin a timezone, do it here.
    return datetime.now()

def parse_relative_date(phrase: str) -> Optional[datetime]:
    """
    Supports: today, yesterday, last N days/weeks/months/years
             before/after YYYY-MM-DD (handled elsewhere)
    """
    s = phrase.lower().strip()
    now = _now()
    if s == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if s == "yesterday":
        d = now - timedelta(days=1)
        return d.replace(hour=0, minute=0, second=0, microsecond=0)

    m = re.search(r"last\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)", s)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if "day" in unit:
            return (now - timedelta(days=n)).replace(hour=0, minute=0, second=0, microsecond=0)
        if "week" in unit:
            return (now - timedelta(weeks=n)).replace(hour=0, minute=0, second=0, microsecond=0)
        if "month" in unit:
            # Approximate months as 30 days (simple, safe default)
            return (now - timedelta(days=30*n)).replace(hour=0, minute=0, second=0, microsecond=0)
        if "year" in unit:
            # Approximate years as 365 days
            return (now - timedelta(days=365*n)).replace(hour=0, minute=0, second=0, microsecond=0)

    return None

def parse_date_literal(text: str) -> Optional[datetime]:
    """
    Try several common formats; returns naive datetime at 00:00:00.
    """
    candidates = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
        "%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d %Y",
        "%Y/%m/%d"
    ]
    for fmt in candidates:
        try:
            d = datetime.strptime(text.strip(), fmt)
            return d.replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            continue
    return parse_relative_date(text)

# --------------------------
# Core parsing utilities
# --------------------------

def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def find_fields_in_text(text: str, schema: Dict[str, str]) -> List[str]:
    hits = []
    low = text.lower()
    for f in schema.keys():
        if re.search(rf"\b{re.escape(f.lower())}\b", low):
            hits.append(f)
    return hits

def extract_numbers(text: str) -> List[float]:
    return [float(x) for x in re.findall(_NUM, text)]

def extract_quoted_strings(text: str) -> List[str]:
    vals = []
    for m in re.finditer(_QUOTED, text):
        vals.append(next(g for g in m.groups() if g is not None))
    return vals

def word_in(text: str, words: List[str]) -> bool:
    t = text.lower()
    return any(w in t for w in words)

def find_word_after(text: str, words: List[str]) -> Optional[str]:
    """
    Returns the substring after the first occurrence of any 'words'.
    """
    t = text.lower()
    for w in words:
        idx = t.find(w)
        if idx >= 0:
            return text[idx + len(w):].strip()
    return None

def detect_limit(text: str) -> Optional[int]:
    # "top N", "bottom N", "first N", "last N", "limit N"
    m = re.search(r"(top|bottom|first|last|limit)\s+(\d+)", text, re.I)
    if m:
        return int(m.group(2))
    return None

def detect_sort(text: str, schema: Dict[str, str]) -> Optional[Tuple[str, int]]:
    """
    Returns (field, direction) with direction 1 for ASC, -1 for DESC.
    Heuristics: "sort by field desc/asc", "highest/lowest field"
    """
    low = text.lower()
    # explicit sort by
    s_after = find_word_after(low, SORT_SYNONYMS)
    if s_after:
        # find the next mentioned field
        for f in schema:
            if re.search(rf"\b{re.escape(f.lower())}\b", s_after):
                direction = -1 if word_in(s_after, DESC_WORDS) else (1 if word_in(s_after, ASC_WORDS) else 1)
                return (f, direction)

    # "highest/lowest <field>"
    for f in schema:
        if re.search(rf"\b(highest|lowest|largest|smallest|max|min|top|bottom)\s+{re.escape(f.lower())}\b", low):
            if word_in(low, ["highest", "largest", "max", "top"]):
                return (f, -1)
            if word_in(low, ["lowest", "smallest", "min", "bottom"]):
                return (f, 1)

    return None

def split_clauses(text: str) -> List[str]:
    # Split on common logical joiners without breaking quoted strings (very light heuristic)
    tmp = text
    for j in LOGICAL_JOINERS:
        tmp = re.sub(rf"\s{re.escape(j)}\s", " | ", tmp, flags=re.I)
    parts = [normalize_spaces(p) for p in tmp.split("|")]
    return [p for p in parts if p]

# --------------------------
# Condition parsing
# --------------------------

def build_value(val_text: str, ftype: str):
    val_text = val_text.strip().strip(",.")
    if ftype == "number":
        try:
            return float(val_text)
        except ValueError:
            pass
    if ftype == "boolean":
        if val_text.lower() in ["true", "yes", "1"]:
            return True
        if val_text.lower() in ["false", "no", "0"]:
            return False
    if ftype == "date":
        dt = parse_date_literal(val_text)
        if dt:
            return dt
    # If quoted remove quotes
    m = re.match(r"^['\"](.*)['\"]$", val_text)
    if m:
        return m.group(1)
    return val_text

def parse_between(clause: str, field: str, ftype: str):
    m = re.search(rf"{re.escape(field)}\s+(?:between)\s+([^\s]+)\s+and\s+([^\s]+)", clause, re.I)
    if m:
        v1 = build_value(m.group(1), ftype)
        v2 = build_value(m.group(2), ftype)
        if ftype == "date":
            # Convert to datetime if possible
            if isinstance(v1, str): v1 = parse_date_literal(v1) or v1
            if isinstance(v2, str): v2 = parse_date_literal(v2) or v2
        return {field: {"$gte": v1, "$lte": v2}}
    return None

def parse_in_list(clause: str, field: str, ftype: str):
    m = re.search(rf"{re.escape(field)}\s+(?:in)\s*\(([^)]*)\)", clause, re.I)
    if m:
        raw = m.group(1)
        parts = [p.strip() for p in re.split(r",\s*", raw) if p.strip()]
        vals = [build_value(p, ftype) for p in parts]
        return {field: {"$in": vals}}
    return None

def parse_contains_like(clause: str, field: str, ftype: str):
    for w in CONTAINS_SYNONYMS:
        m = re.search(rf"{re.escape(field)}\s+{re.escape(w)}\s+(.+)", clause, re.I)
        if m:
            val = build_value(m.group(1), "string")
            return {field: {"$regex": re.escape(str(val)), "$options": "i"}}
    for w in STARTS_WITH_SYNONYMS:
        m = re.search(rf"{re.escape(field)}\s+{re.escape(w)}\s+(.+)", clause, re.I)
        if m:
            val = build_value(m.group(1), "string")
            return {field: {"$regex": f"^{re.escape(str(val))}", "$options": "i"}}
    for w in ENDS_WITH_SYNONYMS:
        m = re.search(rf"{re.escape(field)}\s+{re.escape(w)}\s+(.+)", clause, re.I)
        if m:
            val = build_value(m.group(1), "string")
            return {field: {"$regex": f"{re.escape(str(val))}$", "$options": "i"}}
    return None

def parse_basic_comparators(clause: str, field: str, ftype: str):
    # Order matters: try >=, <=, !=, =, >, <
    pairs = [
        (">=", [" >=", " gte ", " at least ", " greater than or equal "]),
        ("<=", [" <=", " lte ", " at most ", " less than or equal "]),
        ("!=", [" !=", " not equal ", " not equals "]),
        ("=",  [" =", " equal ", " equals ", " is ", " are "]),
        (">",  [" >", " greater than ", " more than ", " over ", " above ", " after "]),
        ("<",  [" <", " less than ", " fewer than ", " under ", " below ", " before "]),
    ]
    low = f" {clause.lower()} "
    for op, hints in pairs:
        for h in hints:
            if h in low:
                # capture right-hand value after the field/op hint
                # flexible regex: field <op-ish> value
                # We’ll just take text after field token
                m = re.search(rf"{re.escape(field)}.*{re.escape(h.strip())}\s*(.+)$", clause, re.I)
                if m:
                    raw = m.group(1)
                    # stop at joiners if present
                    for j in LOGICAL_JOINERS:
                        raw = re.split(rf"\s{re.escape(j)}\s", raw, flags=re.I)[0]
                    val = build_value(raw, ftype)
                    if ftype == "date" and isinstance(val, str):
                        # try relative "today", "yesterday", "last N days"
                        dt = parse_date_literal(val) or parse_relative_date(val)
                        if dt: val = dt
                    mongo_op = {"=":"$eq","!=":"$ne",">":"$gt","<":"$lt",">=":"$gte","<=":"$lte"}[op]
                    return {field: {mongo_op: val}}
    return None

def parse_relative_date_range(clause: str, field: str, ftype: str):
    # e.g., "for last 30 days", "in the last 7 days"
    if ftype != "date":
        return None
    m = re.search(r"(?:for|in)?\s*the?\s*last\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)", clause, re.I)
    if m:
        anchor = parse_relative_date(f"last {m.group(1)} {m.group(2)}")
        if anchor:
            return {field: {"$gte": anchor}}
    # Just "today"/"yesterday"
    m2 = re.search(rf"{re.escape(field)}.*(today|yesterday)$", clause, re.I)
    if m2:
        dt = parse_relative_date(m2.group(1))
        if dt:
            return {field: {"$gte": dt}}
    return None

def parse_conditions(where_text: str, schema: Dict[str, str]) -> Dict[str, Any]:
    query: Dict[str, Any] = {}
    for clause in split_clauses(where_text):
        for field, ftype in schema.items():
            if re.search(rf"\b{re.escape(field)}\b", clause, re.I):
                for parser in (parse_between, parse_in_list, parse_contains_like,
                               parse_relative_date_range, parse_basic_comparators):
                    cond = parser(clause, field, ftype)
                    if cond:
                        query.update(cond)
                        break
    return query

# --------------------------
# Aggregations, grouping, projection
# --------------------------

def detect_aggregations(text: str, schema: Dict[str, str]) -> List[Tuple[str, Optional[str]]]:
    """
    Returns list of tuples (agg_type, field_or_None)
    e.g., [("count", None), ("avg", "amount")]
    """
    low = text.lower()
    aggs: List[Tuple[str, Optional[str]]] = []

    # COUNT without a field
    if any(w in low for w in AGG_WORDS["count"]):
        aggs.append(("count", None))

    # field-bound aggregations
    for f in schema:
        f_pat = rf"(avg|average|mean|min|minimum|max|maximum|sum|total|distinct)\s+(of\s+)?{re.escape(f)}\b"
        for m in re.finditer(f_pat, low):
            word = m.group(1)
            if word in ["avg", "average", "mean"]: aggs.append(("avg", f))
            elif word in ["min", "minimum"]: aggs.append(("min", f))
            elif word in ["max", "maximum"]: aggs.append(("max", f))
            elif word in ["sum", "total"]: aggs.append(("sum", f))
            elif word in ["distinct"]: aggs.append(("distinct", f))

    # Patterns like "highest <field>" or "lowest <field>"
    for f in schema:
        if re.search(rf"\b(highest|max|largest)\s+{re.escape(f)}\b", low):
            aggs.append(("max", f))
        if re.search(rf"\b(lowest|min|smallest)\s+{re.escape(f)}\b", low):
            aggs.append(("min", f))

    # Single-word "average <field>", "sum <field>"
    for f in schema:
        if re.search(rf"\baverage\s+{re.escape(f)}\b", low): aggs.append(("avg", f))
        if re.search(rf"\bsum\s+{re.escape(f)}\b", low): aggs.append(("sum", f))

    # Deduplicate
    seen = set()
    uniq: List[Tuple[str, Optional[str]]] = []
    for a in aggs:
        if a not in seen:
            uniq.append(a); seen.add(a)
    return uniq

def detect_group_by(text: str, schema: Dict[str, str]) -> List[str]:
    low = text.lower()
    fields: List[str] = []
    # Look for "group by ..." / "per ..." / "by ..."
    for kw in GROUP_BY_SYNONYMS:
        m = re.search(rf"{re.escape(kw)}\s+(.+)", low)
        if m:
            tail = m.group(1)
            # collect mentioned fields in the tail
            for f in schema:
                if re.search(rf"\b{re.escape(f.lower())}\b", tail):
                    fields.append(f)
    # Deduplicate keep order
    seen = set(); out = []
    for f in fields:
        if f not in seen:
            out.append(f); seen.add(f)
    return out

def detect_projection(text: str, schema: Dict[str, str]) -> Optional[Dict[str, int]]:
    low = text.lower()
    after = find_word_after(low, PROJECTION_WORDS)
    if not after: 
        return None
    proj_fields = []
    for f in schema:
        if re.search(rf"\b{re.escape(f.lower())}\b", after):
            proj_fields.append(f)
    if proj_fields:
        return {f: 1 for f in proj_fields}
    return None

# --------------------------
# Main entry
# --------------------------

def nlp_to_mongo(prompt: str,
                 schema: Dict[str, str],
                 collection: str = "collection") -> Dict[str, Any]:
    """
    Decide whether to return a find-spec or an aggregation pipeline.
    """
    text = normalize_spaces(prompt)
    where_part = ""
    # Try to isolate "where ..." if present
    m = re.search(r"\bwhere\b(.*)$", text, re.I)
    if m:
        where_part = m.group(1)
    else:
        where_part = text

    # Build $match
    query = parse_conditions(where_part, schema)

    # Detect other parts
    aggs = detect_aggregations(text, schema)
    groups = detect_group_by(text, schema)
    sort = detect_sort(text, schema)
    limit = detect_limit(text)
    projection = detect_projection(text, schema)

    # If aggregation, build pipeline
    wants_agg = bool(aggs or groups or word_in(text.lower(), AGG_WORDS["count"]))

    if wants_agg:
        pipeline: List[Dict[str, Any]] = []
        if query:
            pipeline.append({"$match": query})

        # $group stage
        group_id: Any = None
        if groups:
            group_id = {g: f"${g}" for g in groups}
        else:
            group_id = None  # single bucket

        group_spec: Dict[str, Any] = {"_id": group_id}

        # If "count" requested without field, add $sum:1
        if any(a[0] == "count" for a in aggs) or (not aggs and not groups and "count" in text.lower()):
            group_spec["count"] = {"$sum": 1}

        # Field-bound aggregations
        for a, f in aggs:
            if a == "avg" and f: group_spec[f"avg_{f}"] = {"$avg": f"${f}"}
            if a == "sum" and f: group_spec[f"sum_{f}"] = {"$sum": f"${f}"}
            if a == "min" and f: group_spec[f"min_{f}"] = {"$min": f"${f}"}
            if a == "max" and f: group_spec[f"max_{f}"] = {"$max": f"${f}"}
            if a == "distinct" and f:
                # distinct count via addToSet then size
                group_spec.setdefault("distinct_sets", {}).setdefault(f, {"$addToSet": f"${f}"})

        # If any distinct requested, we need a $group then $project to size the sets
        if "distinct_sets" in group_spec:
            distinct_sets = group_spec.pop("distinct_sets")
            # First group collecting sets
            pipeline.append({"$group": {**group_spec, **{f"set_{k}": v for k, v in distinct_sets.items()}}})
            # Then project sizes
            proj = {"_id": 1}
            for k in distinct_sets.keys():
                proj[f"distinct_count_{k}"] = {"$size": f"$set_{k}"}
            pipeline.append({"$project": proj})
        else:
            pipeline.append({"$group": group_spec})

        # Sorting for aggregated results
        if sort:
            field, direction = sort
            # If sort field is an aggregate alias, prefer that; else sort by grouping key or count
            sort_field = None
            for key in ["avg_", "sum_", "min_", "max_", "distinct_count_", "count"]:
                if key == "count" and "count" in group_spec:
                    sort_field = "count"
                    break
                # find matching aggregate name
                for k in list(group_spec.keys()):
                    if k.startswith(key) and field in k:
                        sort_field = k
                        break
            if not sort_field:
                # fallback: sort by grouping key if exists
                if groups:
                    sort_field = f"_id.{groups[0]}"
                else:
                    sort_field = "count" if "count" in group_spec else None
            if sort_field:
                pipeline.append({"$sort": {sort_field: direction}})

        # Limit
        if limit:
            pipeline.append({"$limit": limit})

        # Optional projection to clean _id if no groups
        if not groups:
            # expose aggregates clearly
            pipeline.append({"$project": {k: 1 for k in group_spec.keys() if k != "_id" and k is not None}})

        return {"type": "aggregate", "collection": collection, "pipeline": pipeline}

    # Otherwise, build a find query
    find_spec: Dict[str, Any] = {"type": "find", "collection": collection, "query": query or {}}
    if projection:
        find_spec["projection"] = projection
    if sort:
        field, direction = sort
        find_spec["sort"] = [(field, direction)]
    if limit:
        find_spec["limit"] = limit
    return find_spec

# --------------------------
# Quick examples (remove or adapt in your app)
# --------------------------
if __name__ == "__main__":
    schema = {
        "amount": "number",
        "category": "string",
        "created_at": "date",
        "status": "string",
        "user_id": "string",
        "region": "string"
    }

    examples = [
        "count orders where status = 'completed' and amount > 100 in the last 7 days",
        "average amount by category for last 30 days where status = completed, top 5",
        "sum of amount where category in ('food','travel') and created_at between 2024-01-01 and 2024-12-31 sort by amount desc",
        "list user_id, amount where amount >= 500 and status != 'failed' sort by created_at desc limit 10",
        "distinct category where region contains 'west'",
        "highest amount by category",
    ]

    for p in examples:
        print("Prompt:", p)
        print(nlp_to_mongo(p, schema, collection="orders"))
        print("-" * 80)