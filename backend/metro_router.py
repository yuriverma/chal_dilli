
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
        if n in self.name_to_stop_ids:
            return self.name_to_stop_ids[n][0]
        q_tokens = token_set(query)
        best_sid, best_score = None, 0.0
        for sid, info in self.stops.items():
            score = jaccard(q_tokens, token_set(info["name"]))
            if score > best_score:
                best_sid, best_score = sid, score
        return best_sid if best_score >= 0.34 else None

    def edge_key(self, u: str, v: str):
        return (u, v) if u < v else (v, u)

    def dijkstra(self, src: str, dst: str):
        import heapq
        INF = 1e18
        dist = defaultdict(lambda: INF); parent = {}
        dist[src] = 0.0; pq = [(0.0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if d != dist[u]: continue
            if u == dst: break
            for v, w in self.adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd; parent[v] = u
                    heapq.heappush(pq, (nd, v))
        if dist[dst] == INF:
            return (INF, [])
        path = [dst]
        while path[-1] != src:
            path.append(parent[path[-1]])
        path.reverse()
        return (dist[dst], path)

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

    def human_route(self, src_name: str, dst_name: str, smart_card: bool=True):
        src_id = self.find_best_station_id(src_name)
        dst_id = self.find_best_station_id(dst_name)
        if not src_id: return {"error": f"Couldn't find station matching '{src_name}'"}
        if not dst_id: return {"error": f"Couldn't find station matching '{dst_name}'"}
        if src_id == dst_id: return {"message": f"You're already at {self.stops[src_id]['name']} 😄"}
        total_km, path = self.dijkstra(src_id, dst_id)
        if not path: return {"error":"No route found between the stations."}
        segs = self.path_segments(path)
        uses_ael = self.path_uses_airport_express(segs)
        est_fare = self.estimate_fare(total_km, uses_ael, smart_card=smart_card)

        lines = [f"Best route ({total_km:.1f} km • est. fare ₹{est_fare}{' with Smart Card' if smart_card else ''}):"]
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
            "estimated_fare": est_fare,
            "smart_card": smart_card,
            "segments": [{
                "line": self.route_display_name(s["route_id"]),
                "from": self.stops[s["from"]]["name"],
                "to": self.stops[s["to"]]["name"],
                "stops": [self.stops[x]["name"] for x in s["stops"]]
            } for s in segs],
            "human_text": "\n".join(lines)
        }
