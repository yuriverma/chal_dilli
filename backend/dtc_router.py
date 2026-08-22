#!/usr/bin/env python3
"""
DTC Bus Router for CHAL DILLI
Provides bus routing using GTFS data from data/GTFS
"""

import csv
import heapq
import math
import os
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between two points in kilometers"""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def norm(s: str) -> str:
    """Normalize stop name for matching"""
    s = s.lower().strip()
    for token in [" bus stop", " bus stand", " stop", " stand", " (delhi)", "(delhi)"]:
        s = s.replace(token, "")
    s = s.replace("-", " ").replace("_", " ")
    s = " ".join(s.split())
    return s

def token_set(s: str) -> set:
    """Convert string to set of tokens"""
    return set([t for t in norm(s).split() if t])

def jaccard(a: set, b: set) -> float:
    """Calculate Jaccard similarity between two sets"""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

class DTCRouter:
    def __init__(self, gtfs_dir: str):
        """Initialize DTC router with GTFS data directory"""
        self.gtfs_dir = gtfs_dir
        # Common stop aliases
        self.stop_aliases: Dict[str, str] = {
            "cp": "connaught place",
            "connaught place": "connaught place",
            "kashmere gate": "kashmere gate",
            "dwarka": "dwarka",
            "saket": "saket",
            "karol bagh": "karol bagh",
            "rajiv chowk": "connaught place",
        }
        # Routing parameters
        self.avg_speed_kmph = 25.0  # Average bus speed in km/h
        self.per_stop_dwell_min = 0.5  # Time spent at each stop
        self.transfer_penalty_min = 5.0  # Penalty for bus transfers
        self._load()

    def _load(self):
        """Load GTFS data files"""
        stops_path = os.path.join(self.gtfs_dir, "stops.csv")
        routes_path = os.path.join(self.gtfs_dir, "routes.csv")
        trips_path = os.path.join(self.gtfs_dir, "trips.csv")
        stop_times_path = os.path.join(self.gtfs_dir, "stop_times.csv")

        # Load stops
        self.stops = {}
        self.name_to_stop_ids = defaultdict(list)
        with open(stops_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                sid = r["stop_id"]
                name = r["stop_name"]
                try:
                    lat = float(r["stop_lat"])
                    lon = float(r["stop_lon"])
                    self.stops[sid] = {"name": name, "lat": lat, "lon": lon}
                    self.name_to_stop_ids[norm(name)].append(sid)
                except (ValueError, KeyError):
                    continue

        # Load routes
        self.routes = {}
        with open(routes_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rid = r["route_id"]
                self.routes[rid] = {
                    "short_name": r.get("route_short_name") or "",
                    "long_name": r.get("route_long_name") or "",
                    "type": r.get("route_type") or "",
                }

        # The stop-to-stop graph. Prefer the precomputed edge list: the raw feed
        # expresses it as 2.25M stop_times rows (one per stop per departure)
        # that collapse to 6,187 unique edges, so rebuilding it on every boot
        # parses 76MB to derive 140KB. scripts/build_bus_graph.py regenerates
        # the edge list from a full feed; only the edge list is committed.
        edges_path = os.path.join(self.gtfs_dir, "bus_edges.csv")
        if os.path.exists(edges_path):
            self._load_edges(edges_path)
        else:
            self._build_edges_from_stop_times(trips_path, stop_times_path)

        # Build adjacency list from the edges, however they were obtained.
        self.adj = defaultdict(list)
        for (u, v), w in self.edge_weight.items():
            self.adj[u].append((v, w))
            self.adj[v].append((u, w))

    def _load_edges(self, edges_path: str):
        """Load the precomputed stop-to-stop graph."""
        self.edge_weight = {}
        self.edge_route_main = {}
        with open(edges_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                u = r["from_stop_id"]
                v = r["to_stop_id"]
                # A stop dropped from stops.csv since the graph was built would
                # otherwise become an edge to nowhere.
                if u not in self.stops or v not in self.stops:
                    continue
                try:
                    self.edge_weight[(u, v)] = float(r["distance_km"])
                except (ValueError, KeyError):
                    continue
                if r.get("route_id"):
                    self.edge_route_main[(u, v)] = r["route_id"]

    def _build_edges_from_stop_times(self, trips_path: str, stop_times_path: str):
        """Derive the graph from a raw GTFS feed.

        Fallback for when bus_edges.csv is absent — kept so a freshly
        downloaded feed works without running the build script first. Must stay
        equivalent to scripts/build_bus_graph.py.
        """
        trip_route = {}
        with open(trips_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                trip_route[r["trip_id"]] = r["route_id"]

        trip_stops = defaultdict(list)
        with open(stop_times_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    trip_stops[r["trip_id"]].append(
                        (int(r["stop_sequence"]), r["stop_id"])
                    )
                except (ValueError, KeyError):
                    continue
        for tid in list(trip_stops.keys()):
            trip_stops[tid].sort()

        self.edge_weight = {}
        edge_route_counter = defaultdict(Counter)
        for trip_id, seqs in trip_stops.items():
            r_id = trip_route.get(trip_id)
            if not r_id:
                continue
            for i in range(len(seqs) - 1):
                a = seqs[i][1]
                b = seqs[i+1][1]
                if a == b or a not in self.stops or b not in self.stops:
                    continue
                u, v = (a, b) if a < b else (b, a)
                d = haversine_km(
                    self.stops[u]["lat"], self.stops[u]["lon"],
                    self.stops[v]["lat"], self.stops[v]["lon"]
                )
                if (u, v) not in self.edge_weight or d < self.edge_weight[(u, v)]:
                    self.edge_weight[(u, v)] = d
                edge_route_counter[(u, v)][r_id] += 1

        self.edge_route_main = {}
        for uv, counter in edge_route_counter.items():
            if counter:
                self.edge_route_main[uv] = counter.most_common(1)[0][0]

    def route_display_name(self, route_id: str) -> str:
        """Get display name for a route"""
        r = self.routes.get(route_id, {})
        for key in ["long_name", "short_name"]:
            if r.get(key):
                return r[key]
        return f"Route {route_id}"

    def edge_key(self, u: str, v: str):
        """Get canonical edge key"""
        return (u, v) if u < v else (v, u)

    def edge_time_minutes(self, u: str, v: str) -> float:
        """Estimate minutes to traverse edge (u,v) including dwell time"""
        edge_key = self.edge_key(u, v)
        if edge_key not in self.edge_weight:
            return float('inf')
        w = self.edge_weight[edge_key]
        run_time = (w / self.avg_speed_kmph) * 60.0
        return run_time + self.per_stop_dwell_min

    def dijkstra_time(self, src: str, dst: str):
        """Dijkstra algorithm minimizing travel time with transfer penalties"""
        INF = 1e18
        # state: (node_id, current_route_id)
        start_state = (src, None)
        dist = defaultdict(lambda: INF)
        parent = {}
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

        # Reconstruct path
        path_nodes = [best_goal[0]]
        cur = best_goal
        while cur in parent:
            prev = parent[cur]
            path_nodes.append(prev[0])
            cur = prev
        path_nodes.reverse()
        return (best_goal_cost, path_nodes)

    def path_segments(self, path: List[str]):
        """Break path into segments by route"""
        if len(path) < 2:
            return []
        segs = []
        cur_route = None
        cur_start = path[0]
        cur_stops = [path[0]]
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            r_id = self.edge_route_main.get(self.edge_key(u, v))
            if cur_route is None:
                cur_route = r_id
            if r_id != cur_route:
                segs.append({
                    "route_id": cur_route,
                    "from": cur_start,
                    "to": path[i],
                    "stops": cur_stops[:]
                })
                cur_route = r_id
                cur_start = path[i]
                cur_stops = [path[i]]
            cur_stops.append(v)
        
        segs.append({
            "route_id": cur_route,
            "from": cur_start,
            "to": path[-1],
            "stops": cur_stops[:]
        })
        return segs

    def find_best_stop_id(self, query: str) -> Optional[str]:
        """Find best matching stop ID for a query string"""
        n = norm(query)
        # Apply alias mapping first
        if n in self.stop_aliases:
            n = norm(self.stop_aliases[n])

        # Exact normalized match
        if n in self.name_to_stop_ids:
            return self.name_to_stop_ids[n][0]

        # Try condensed match (ignore spaces)
        condensed = n.replace(" ", "")
        for name_norm, ids in self.name_to_stop_ids.items():
            if name_norm.replace(" ", "") == condensed:
                return ids[0]

        # Fuzzy matching using Jaccard similarity
        q_tokens = token_set(query)
        best_sid, best_score = None, 0.0
        for sid, info in self.stops.items():
            score = jaccard(q_tokens, token_set(info["name"]))
            if score > best_score:
                best_sid, best_score = sid, score

        # Threshold for fuzzy matching
        return best_sid if best_score >= 0.25 else None

    def get_route(self, source_name: str, destination_name: str) -> Dict:
        """Get route from source to destination"""
        src_id = self.find_best_stop_id(source_name)
        dst_id = self.find_best_stop_id(destination_name)
        
        if not src_id:
            return {"error": f"Couldn't find stop matching '{source_name}'"}
        if not dst_id:
            return {"error": f"Couldn't find stop matching '{destination_name}'"}
        if src_id == dst_id:
            return {"message": f"You're already at {self.stops[src_id]['name']} 😄"}

        total_min, path = self.dijkstra_time(src_id, dst_id)
        if not path or total_min >= 1e17:
            return {"error": "No route found between the stops."}

        # Compute total distance
        total_km = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            edge_key = self.edge_key(u, v)
            if edge_key in self.edge_weight:
                total_km += self.edge_weight[edge_key]

        segs = self.path_segments(path)

        # Format human-readable response
        lines = [
            f"Best DTC bus route (~{int(round(total_min))} min • {total_km:.1f} km):"
        ]
        for idx, s in enumerate(segs, start=1):
            rname = self.route_display_name(s["route_id"]) or "Bus Route"
            start_name = self.stops[s["from"]]["name"]
            end_name = self.stops[s["to"]]["name"]
            hop_count = len(s["stops"]) - 1
            if idx == 1:
                lines.append(f"{idx}. Board {rname} at {start_name}, go {hop_count} stop(s) → alight at {end_name}.")
            else:
                lines.append(f"{idx}. Transfer at {start_name} → {rname}, ride {hop_count} stop(s) → {end_name}.")

        return {
            "from": self.stops[src_id]["name"],
            "to": self.stops[dst_id]["name"],
            "distance_km": round(total_km, 2),
            "duration_min": int(round(total_min)),
            "segments": [{
                "route": self.route_display_name(s["route_id"]),
                "from": self.stops[s["from"]]["name"],
                "to": self.stops[s["to"]]["name"],
                "stops": [self.stops[x]["name"] for x in s["stops"]]
            } for s in segs],
            "human_text": "\n".join(lines)
        }

    def autocomplete_stop_names(self, prefix: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions for stop names"""
        prefix_norm = norm(prefix)
        matches = []
        seen = set()
        
        for stop_id, info in self.stops.items():
            name_norm = norm(info["name"])
            if name_norm.startswith(prefix_norm) or prefix_norm in name_norm:
                if info["name"] not in seen:
                    matches.append(info["name"])
                    seen.add(info["name"])
                if len(matches) >= limit:
                    break
        
        return matches[:limit]

    def find_nearest_stop(self, lat: float, lon: float, max_distance_km: float = 5.0) -> Optional[Dict]:
        """Find nearest stop to given coordinates"""
        best_stop = None
        best_distance = float('inf')
        
        for stop_id, info in self.stops.items():
            dist = haversine_km(lat, lon, info["lat"], info["lon"])
            if dist < best_distance and dist <= max_distance_km:
                best_distance = dist
                best_stop = {
                    "stop_id": stop_id,
                    "name": info["name"],
                    "lat": info["lat"],
                    "lon": info["lon"],
                    "distance_km": dist
                }
        
        return best_stop


