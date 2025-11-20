
# metro_router.py
import os, csv, math
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Set

def haversine_km(lat1, lon1, lat2, lon2):
    import math
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def norm(s: str) -> str:
    s = s.lower().strip()
    for token in [" metro station", " metro stn", " station", " (delhi)", "(delhi)"]:
        s = s.replace(token, "")
    s = s.replace("-", " ").replace("_", " ")
    s = " ".join(s.split())
    return s

def token_set(s: str) -> set:
    return set([t for t in norm(s).split() if t])

def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

class MetroRouter:
    def __init__(self, gtfs_dir: str):
        self.gtfs_dir = gtfs_dir
        # Common aliases to improve station matching (lowercased canonical forms)
        self.station_aliases: Dict[str, str] = {
            "aerocity": "delhi aerocity",
            "aero city": "delhi aerocity",
            "igi airport": "igi airport",
            "airport": "igi airport",
            "cp": "rajiv chowk",
            "connaught place": "rajiv chowk",
            "janakpuri west": "janak puri west",
            "janakpuri w": "janak puri west",
            "janak puri w": "janak puri west",
            "peeragarhi": "peera garhi",
            "peera garhi": "peera garhi",
            "uttamnagar east": "uttam nagar east",
            "uttamnagar west": "uttam nagar west",
        }
        # Routing time model parameters
        self.avg_speed_kmph_regular = 32.0
        self.avg_speed_kmph_airport = 60.0
        self.per_stop_dwell_min = 0.5
        self.transfer_penalty_min = 7.0
        # Extra penalty to discourage Airport Express when preferring low fare
        self.extra_airport_penalty_min = 0.0
        self._load()

    def _load(self):
        stops_path = os.path.join(self.gtfs_dir, "stops.txt")
        routes_path = os.path.join(self.gtfs_dir, "routes.txt")
        trips_path = os.path.join(self.gtfs_dir, "trips.txt")
        stop_times_path = os.path.join(self.gtfs_dir, "stop_times.txt")

        # Load stops
        self.stops = {}
        self.name_to_stop_ids = defaultdict(list)
        import csv
        with open(stops_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                sid = r["stop_id"]
                name = r["stop_name"]
                lat = float(r["stop_lat"]); lon = float(r["stop_lon"])
                self.stops[sid] = {"name": name, "lat": lat, "lon": lon}
                self.name_to_stop_ids[norm(name)].append(sid)

        # Load routes
        self.routes = {}
        with open(routes_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rid = r["route_id"]
                self.routes[rid] = {
                    "short_name": r.get("route_short_name") or "",
                    "long_name": r.get("route_long_name") or "",
                    "desc": r.get("route_desc") or "",
                    "type": r.get("route_type") or "",
                }

        # Trips -> route_id
        self.trip_route = {}
        with open(trips_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                self.trip_route[r["trip_id"]] = r["route_id"]

        # Trip stop sequences
        self.trip_stops = defaultdict(list)
        with open(stop_times_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                tid = r["trip_id"]; sid = r["stop_id"]; seq = int(r["stop_sequence"])
                self.trip_stops[tid].append((seq, sid))
        for tid in list(self.trip_stops.keys()):
            self.trip_stops[tid].sort()

        # Build edges
        self.edge_weight = {}
        self.edge_route_counter = defaultdict(Counter)
        for trip_id, seqs in self.trip_stops.items():
            r_id = self.trip_route[trip_id]
            for i in range(len(seqs)-1):
                a = seqs[i][1]; b = seqs[i+1][1]
                if a == b or a not in self.stops or b not in self.stops: continue
                u, v = (a, b) if a < b else (b, a)
                d = haversine_km(self.stops[u]["lat"], self.stops[u]["lon"],
                                 self.stops[v]["lat"], self.stops[v]["lon"])
                if (u, v) not in self.edge_weight or d < self.edge_weight[(u, v)]:
                    self.edge_weight[(u, v)] = d
                self.edge_route_counter[(u, v)][r_id] += 1

        # adjacency & main route per edge
        self.adj = defaultdict(list)
        self.edge_route_main = {}
        for (u, v), w in self.edge_weight.items():
            self.adj[u].append((v, w)); self.adj[v].append((u, w))
            rid = self.edge_route_counter[(u, v)].most_common(1)[0][0]
            self.edge_route_main[(u, v)] = rid

    def route_display_name(self, route_id: str) -> str:
        r = self.routes.get(route_id, {})
        for key in ["long_name", "short_name", "desc"]:
            if r.get(key): return r[key]
        return route_id

    def token_set(self, s: str) -> set:
        return token_set(s)

    def find_best_station_id(self, query: str) -> Optional[str]:
        n = norm(query)
        # Apply alias mapping first
        alias_key = n
        if alias_key in self.station_aliases:
            n = norm(self.station_aliases[alias_key])

        # Exact normalized match
        if n in self.name_to_stop_ids:
            return self.name_to_stop_ids[n][0]

        # Try condensed match (ignore spaces)
        condensed = n.replace(" ", "")
        for name_norm, ids in self.name_to_stop_ids.items():
            if name_norm.replace(" ", "") == condensed:
                return ids[0]

        q_tokens = token_set(query)
        best_sid, best_score = None, 0.0
        for sid, info in self.stops.items():
            score = jaccard(q_tokens, token_set(info["name"]))
            if score > best_score:
                best_sid, best_score = sid, score
        # Slightly relaxed threshold to accept common variants
        return best_sid if best_score >= 0.28 else None

    def edge_key(self, u: str, v: str):
        return (u, v) if u < v else (v, u)

    def edge_time_minutes(self, u: str, v: str) -> float:
        """Estimate minutes to traverse edge (u,v) including dwell time."""
        w = self.edge_weight[self.edge_key(u, v)]
        r_id = self.edge_route_main.get(self.edge_key(u, v))
        rname = (self.route_display_name(r_id) or "").lower() if r_id else ""
        speed = self.avg_speed_kmph_airport if "airport" in rname else self.avg_speed_kmph_regular
        run_time = (w / speed) * 60.0
        extra = self.extra_airport_penalty_min if ("airport" in rname) else 0.0
        return run_time + self.per_stop_dwell_min + extra

    def dijkstra_time(self, src: str, dst: str):
        """Dijkstra minimizing travel time with transfer penalties."""
        import heapq
        INF = 1e18
        # state: (node_id, current_route_id)
        start_state = (src, None)
        dist = defaultdict(lambda: INF)
        parent = {}  # (node, route) -> (prev_node, prev_route)
        dist[start_state] = 0.0
        pq = [(0.0, start_state)]
        best_goal = None
        best_goal_cost = INF
        while pq:
            d, (u, r_prev) = heapq.heappop(pq)
            if d != dist[(u, r_prev)]:
                continue
            if u == dst and d < best_goal_cost:
                best_goal = (u, r_prev)
                best_goal_cost = d
            for v, _w in self.adj[u]:
                r_edge = self.edge_route_main.get(self.edge_key(u, v))
                time_uv = self.edge_time_minutes(u, v)
                transfer_cost = 0.0 if (r_prev is None or r_prev == r_edge) else self.transfer_penalty_min
                nd = d + transfer_cost + time_uv
                state_v = (v, r_edge)
                if nd < dist[state_v]:
                    dist[state_v] = nd
                    parent[state_v] = (u, r_prev)
                    heapq.heappush(pq, (nd, state_v))
        if best_goal is None:
            return (INF, [])
        # reconstruct
        path_nodes = [best_goal[0]]
        cur = best_goal
        while cur in parent:
            prev = parent[cur]
            path_nodes.append(prev[0])
            cur = prev
        path_nodes.reverse()
        return (best_goal_cost, path_nodes)

    def path_segments(self, path: List[str]):
        if len(path) < 2: return []
        segs = []
        cur_route = None; cur_start = path[0]; cur_stops = [path[0]]
        for i in range(len(path)-1):
            u, v = path[i], path[i+1]
            r_id = self.edge_route_main.get(self.edge_key(u, v))
            if cur_route is None: cur_route = r_id
            if r_id != cur_route:
                segs.append({"route_id": cur_route, "from": cur_start, "to": path[i], "stops": cur_stops[:]})
                cur_route = r_id; cur_start = path[i]; cur_stops = [path[i]]
            cur_stops.append(v)
        segs.append({"route_id": cur_route, "from": cur_start, "to": path[-1], "stops": cur_stops[:]})
        return segs

    def path_uses_airport_express(self, segs):
        for s in segs:
            name = self.route_display_name(s["route_id"]).lower()
            if "airport" in name:
                return True
        return False

    def estimate_fare(self, distance_km: float, uses_airport_express: bool, smart_card: bool=True) -> int:
        FARE_SLABS = [(2,10),(5,20),(12,30),(21,40),(32,50),(10**9,60)]
        base = 60
        for limit, fare in FARE_SLABS:
            if distance_km <= limit:
                base = fare; break
        if uses_airport_express and base < 70:
            base = max(base, 70)
        if smart_card:
            base = int((base * 0.9)//1)
        return int(base)

    def human_route(self, src_name: str, dst_name: str, smart_card: bool=True, airport_penalty_min: float=0.0):
        src_id = self.find_best_station_id(src_name)
        dst_id = self.find_best_station_id(dst_name)
        if not src_id: return {"error": f"Couldn't find station matching '{src_name}'"}
        if not dst_id: return {"error": f"Couldn't find station matching '{dst_name}'"}
        if src_id == dst_id: return {"message": f"You're already at {self.stops[src_id]['name']} 😄"}
        # apply temporary airport penalty preference
        prev_penalty = self.extra_airport_penalty_min
        try:
            self.extra_airport_penalty_min = max(0.0, float(airport_penalty_min))
        except Exception:
            self.extra_airport_penalty_min = prev_penalty
        total_min, path = self.dijkstra_time(src_id, dst_id)
        # reset penalty
        self.extra_airport_penalty_min = prev_penalty
        if not path: return {"error":"No route found between the stations."}
        # compute total distance along chosen path
        total_km = 0.0
        for i in range(len(path)-1):
            u, v = path[i], path[i+1]
            total_km += self.edge_weight[self.edge_key(u, v)]
        segs = self.path_segments(path)
        uses_ael = self.path_uses_airport_express(segs)
        est_fare = self.estimate_fare(total_km, uses_ael, smart_card=smart_card)

        lines = [
            f"Best route (~{int(round(total_min))} min • {total_km:.1f} km • est. fare ₹{est_fare}{' with Smart Card' if smart_card else ''}):"
        ]
        for idx, s in enumerate(segs, start=1):
            rname = self.route_display_name(s["route_id"]) or "Metro Line"
            start_name = self.stops[s["from"]]["name"]; end_name = self.stops[s["to"]]["name"]
            hop_count = len(s["stops"])-1
            if idx == 1:
                lines.append(f"{idx}. Board {rname} at {start_name}, go {hop_count} stop(s) → alight at {end_name}.")
            else:
                lines.append(f"{idx}. Interchange at {start_name} → {rname}, ride {hop_count} stop(s) → {end_name}.")
        if uses_ael:
            lines.append("Note: Route uses Airport Express Line — fares may be higher (up to ~₹70).")

        return {
            "from": self.stops[src_id]["name"],
            "to": self.stops[dst_id]["name"],
            "distance_km": round(total_km,2),
            "duration_min": int(round(total_min)),
            "estimated_fare": est_fare,
            "uses_airport_express": uses_ael,
            "smart_card": smart_card,
            "segments": [{
                "line": self.route_display_name(s["route_id"]),
                "from": self.stops[s["from"]]["name"],
                "to": self.stops[s["to"]]["name"],
                "stops": [self.stops[x]["name"] for x in s["stops"]]
            } for s in segs],
            "human_text": "\n".join(lines)
        }
