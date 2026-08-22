#!/usr/bin/env python3
"""
Precompute the DTC bus graph from a raw GTFS feed.

Why this exists
---------------
The DTC feed's stop_times.csv is 76MB and 2.25 million rows, and the router
reads exactly three of its five columns -- trip_id, stop_id, stop_sequence.
The arrival and departure times are never looked at. All those rows exist to
express "this trip visits these stops in this order", repeated once per
departure, and the router collapses them into a set of unique stop-to-stop
edges: 6,187 of them.

Shipping the 76MB feed to reconstruct a 150KB graph on every boot is a poor
trade three times over. It is slow to load, it costs memory to parse, and a
single file that large is over the per-file limit for non-LFS files on a
Hugging Face Space's git remote, which is where this deploys.

So the derived graph is committed instead, and this script is how it is
rebuilt when the feed is refreshed.

Usage
-----
    python scripts/build_bus_graph.py data/GTFS

Reads stops.csv, trips.csv and stop_times.csv from that directory and writes
bus_edges.csv beside them. Requires the full feed, which is not in the repo --
download a current one from the DTC/OTD open data portal first.

The output is intentionally a plain sorted CSV: it diffs legibly, so a feed
refresh shows up in review as the routes that actually changed.
"""

import argparse
import csv
import math
import os
import sys
from collections import Counter, defaultdict

EARTH_RADIUS_KM = 6371.0

# Must stay identical to backend/dtc_router.py. The graph is only equivalent to
# the one built at runtime if the distances match exactly.
def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def load_stops(gtfs_dir):
    stops = {}
    with open(os.path.join(gtfs_dir, "stops.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                stops[r["stop_id"]] = (float(r["stop_lat"]), float(r["stop_lon"]))
            except (ValueError, KeyError):
                continue
    return stops


def load_trip_routes(gtfs_dir):
    trip_route = {}
    with open(os.path.join(gtfs_dir, "trips.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            trip_route[r["trip_id"]] = r["route_id"]
    return trip_route


def load_trip_stops(gtfs_dir):
    """trip_id -> [(sequence, stop_id), ...], sorted by sequence."""
    trip_stops = defaultdict(list)
    path = os.path.join(gtfs_dir, "stop_times.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                trip_stops[r["trip_id"]].append((int(r["stop_sequence"]), r["stop_id"]))
            except (ValueError, KeyError):
                continue
    for tid in trip_stops:
        trip_stops[tid].sort()
    return trip_stops


def build_edges(stops, trip_route, trip_stops):
    """Collapse trip stop sequences into undirected unique edges.

    Mirrors dtc_router._load exactly: the edge key is the stop-id pair in
    lexical order, the weight is the shortest distance seen for that pair, and
    the route recorded is whichever serves the pair most often.
    """
    edge_weight = {}
    edge_routes = defaultdict(Counter)

    for trip_id, seqs in trip_stops.items():
        route_id = trip_route.get(trip_id)
        if not route_id:
            continue
        for i in range(len(seqs) - 1):
            a, b = seqs[i][1], seqs[i + 1][1]
            if a == b or a not in stops or b not in stops:
                continue
            u, v = (a, b) if a < b else (b, a)
            d = haversine_km(stops[u][0], stops[u][1], stops[v][0], stops[v][1])
            if (u, v) not in edge_weight or d < edge_weight[(u, v)]:
                edge_weight[(u, v)] = d
            edge_routes[(u, v)][route_id] += 1

    return edge_weight, edge_routes


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("gtfs_dir", help="directory holding the raw GTFS csv files")
    ap.add_argument("-o", "--out", default=None, help="output path")
    args = ap.parse_args()

    out_path = args.out or os.path.join(args.gtfs_dir, "bus_edges.csv")

    missing = [
        n for n in ("stops.csv", "trips.csv", "stop_times.csv")
        if not os.path.exists(os.path.join(args.gtfs_dir, n))
    ]
    if missing:
        sys.exit(
            f"missing from {args.gtfs_dir}: {', '.join(missing)}\n"
            "This needs the full raw GTFS feed, which is not committed -- only "
            "the derived bus_edges.csv is. Download a current feed first."
        )

    print("reading stops...", flush=True)
    stops = load_stops(args.gtfs_dir)
    print(f"  {len(stops):,} stops with coordinates")

    print("reading trips...", flush=True)
    trip_route = load_trip_routes(args.gtfs_dir)
    print(f"  {len(trip_route):,} trips")

    print("reading stop_times (this is the slow part)...", flush=True)
    trip_stops = load_trip_stops(args.gtfs_dir)
    print(f"  {len(trip_stops):,} trips with stop sequences")

    print("collapsing to unique edges...", flush=True)
    edge_weight, edge_routes = build_edges(stops, trip_route, trip_stops)

    # Sorted so the file is stable across runs and diffs meaningfully.
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["from_stop_id", "to_stop_id", "distance_km", "route_id"])
        for (u, v) in sorted(edge_weight):
            main_route = ""
            if edge_routes[(u, v)]:
                main_route = edge_routes[(u, v)].most_common(1)[0][0]
            # 6dp is ~0.1m, far finer than the edge times derived from it.
            w.writerow([u, v, f"{edge_weight[(u, v)]:.6f}", main_route])

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    raw_mb = os.path.getsize(os.path.join(args.gtfs_dir, "stop_times.csv")) / 1024 / 1024
    print()
    print(f"wrote {out_path}")
    print(f"  {len(edge_weight):,} edges, {size_mb:.2f} MB")
    print(f"  replaces {raw_mb:.0f} MB of stop_times.csv ({raw_mb / size_mb:.0f}x smaller)")


if __name__ == "__main__":
    main()
