
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import time
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from common.observability import MetricsMiddleware, metrics_asgi_app

app = FastAPI(title="POC2 Routing")
app.add_middleware(MetricsMiddleware)
app.mount("/metrics", metrics_asgi_app())

class Point(BaseModel):
    id: int
    lat: float
    lon: float

class Job(BaseModel):
    jobId: str
    points: List[Point]

def fake_distance(a: Point, b: Point):
    # Distancia Manhattan simplificada
    return int(abs(a.lat-b.lat)*100000 + abs(a.lon-b.lon)*100000)

@app.post("/routes/solve")
def solve(job: Job):
    start = time.time()
    n = len(job.points)
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def dist_cb(from_index, to_index):
        f = job.points[manager.IndexToNode(from_index)]
        t = job.points[manager.IndexToNode(to_index)]
        return fake_distance(f, t)

    transit_index = routing.RegisterTransitCallback(dist_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_index)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.time_limit.FromSeconds(2)

    solution = routing.EnsureFeasibility(search_params)
    if solution is None:
        solution = routing.SolveWithParameters(search_params)
    elapsed = time.time() - start
    return {"jobId": job.jobId, "points": n, "elapsed": elapsed}
