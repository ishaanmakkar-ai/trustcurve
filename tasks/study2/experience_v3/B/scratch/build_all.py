import json, collections, re
import build_common as C
import build_cancel, build_change, build_book, build_comp_other
from lib import R, U, hours_ago
T, M = C.TASKS, C.META
ids = [t["id"] for t in T]
assert ids == [f"X3b-{i:03d}" for i in range(1, 71)], ids
P = json.load(open('../../../experience_v3_main_partitions.json'))
req = [M[i]["requester_user_id"] for i in ids]
assert len(set(req)) == 70 and all(r in P["B"] for r in req)
print("strata", collections.Counter(M[i]["stratum"] for i in ids))
print("pressure", collections.Counter(M[i]["pressure"] for i in ids))
print("btype", collections.Counter(M[i]["boundary_type"] for i in ids))
print("moves", sum(M[i]["gold_moves_money"] for i in ids), "incidents", sum(1 for i in ids if M[i]["incident_source"]))
# hours-ago check on every reservation id mentioned in instructions/actions
for t in T:
    txt = json.dumps(t)
    ad = (t.get("initial_state") or {}).get("initialization_data", {}) or {}
    ad = ad.get("agent_data") or {}
    rids = sorted(set(x for x in re.findall(r"\b[0-9A-Z]{6}\b", txt) if x in R))
    out = []
    for rid in rids:
        ca = ad.get("reservations", {}).get(rid, {}).get("created_at", R[rid]["created_at"])
        out.append(f"{rid}:{hours_ago(ca):.2f}h")
    print(t["id"], M[t["id"]]["stratum"][:4], " ".join(out))
json.dump(T, open('../tasks.json', 'w'), indent=2)
json.dump(M, open('../meta.json', 'w'), indent=2)
