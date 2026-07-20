"""Exact E(n,k) envelope for graphs containing a fixed K1,4 + 2K2.

Uses scipy.optimize.milp.  The pattern may be fixed on vertices 0..8 because
any copy in a feasible graph can be relabelled to this one.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix


PATTERN = {(0, 1), (0, 2), (0, 3), (0, 4), (5, 6), (7, 8)}


def solve(n: int, m: int) -> dict:
    edges = list(itertools.combinations(range(n), 2))
    edge_id = {e: i for i, e in enumerate(edges)}
    triangles = list(itertools.combinations(range(n), 3))
    ne, nt = len(edges), len(triangles)

    # Variables x_e and y_T.  Maximize sum y_T subject to y_T <= x_e
    # for each of its three edges.  Cardinality is exactly m.
    c = np.r_[np.zeros(ne), -np.ones(nt)]
    rows = 3 * nt + 1
    A = lil_matrix((rows, ne + nt), dtype=float)
    ub = np.zeros(rows)
    row = 0
    for j, tri in enumerate(triangles):
        for e in itertools.combinations(tri, 2):
            A[row, ne + j] = 1
            A[row, edge_id[tuple(sorted(e))]] = -1
            row += 1
    A[row, :ne] = 1
    lb = np.r_[np.zeros(rows - 1), m]
    ub[-1] = m

    lower = np.zeros(ne + nt)
    upper = np.ones(ne + nt)
    for e in PATTERN:
        lower[edge_id[e]] = 1

    res = milp(
        c,
        integrality=np.ones(ne + nt),
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(A.tocsr(), lb, ub),
        options={"time_limit": 120, "mip_rel_gap": 0.0},
    )
    if not res.success:
        raise RuntimeError(f"n={n}, m={m}: {res.message}")
    chosen = [list(edges[i]) for i, value in enumerate(res.x[:ne]) if value > .5]
    return {"n": n, "m": m, "max_triangles": int(round(-res.fun)), "edges": chosen}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, choices=(9, 10))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    results = [solve(args.n, m) for m in range(6, args.n * (args.n - 1) // 2 + 1)]
    args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("n,m,max_triangles")
    for x in results:
        print(x["n"], x["m"], x["max_triangles"], sep=",")


if __name__ == "__main__":
    main()
