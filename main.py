from pprint import pprint
from gurobipy import *
from gurobipy import GRB
import matplotlib.pyplot as plt


def idx(x): return x[0] + x[1] * len(pcb[0])


pcb = [
    "1................5",
    "..................",
    "2...1.....5......6",
    "....2.....6...9...",
    "....3.....7.......",
    "3...4.....8......7",
    "..............9...",
    "..................",
    "4................8",
]
n, m = len(pcb), len(pcb[0])

capacity = {}
commodities = set()
nodes = []

for y in range(n):
    for x in range(m):
        nodes.append(str(idx((x, y))))

        if pcb[y][x] != ".":
            commodities.add(pcb[y][x])

        for dx, dy in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
            xx = x + dx
            yy = y + dy

            if 0 <= xx < m and 0 <= yy < n:
                capacity[(str(idx((x, y))), str(idx((xx, yy))))] = 1000000

commodities = list(commodities)
arcs, capacity = multidict(capacity)

arcs = tuplelist(arcs)

cost = {}
for x in commodities:
    for y in capacity:
        cost[(x, *y)] = 1

inflow = {}
used = set()
cnt = {}

for y in range(n):
    for x in range(m):
        if not pcb[y][x] in cnt:
            cnt[pcb[y][x]] = 0
        cnt[pcb[y][x]] += 1

for y in range(n):
    for x in range(m):
        if pcb[y][x] == ".":
            for z in commodities:
                inflow[(z, str(idx((x, y))))] = 0
        else:
            for z in commodities:
                if z != pcb[y][x]:
                    inflow[(z, str(idx((x, y))))] = 0

            if not pcb[y][x] in used:
                inflow[(pcb[y][x], str(idx((x, y))))] = -(cnt[pcb[y][x]] - 1)
                used.add(pcb[y][x])
            else:
                inflow[(pcb[y][x], str(idx((x, y))))] = 1

# Create optimization model
gpm = Model('netflow')

# Create variables
flow = {}
for h in commodities:
    for i, j in arcs:
        flow[h, i, j] = gpm.addVar(vtype=GRB.INTEGER, ub=capacity[i, j], obj=cost[h, i, j],
                                   name='flow_%s_%s_%s' % (h, i, j))
gpm.update()

# Arc capacity constraints
for i, j in arcs:
    gpm.addConstr(quicksum(flow[h, i, j] for h in commodities) <= capacity[i, j],
                  'cap_%s_%s' % (i, j))

# Flow conservation constraints
for h in commodities:
    for j in nodes:
        gpm.addConstr(
            quicksum(flow[h, i, j] for i, j in arcs.select('*', j)) +
            inflow[h, j] ==
            quicksum(flow[h, j, k] for j, k in arcs.select(j, '*')),
            'node_%s_%s' % (h, j))


# Only one inflow constraints
for j in nodes:
    sums = []
    for h in commodities:
        s = gpm.addVar(name="temp")
        gpm.addConstr(quicksum(flow[h, _j, _k] for _j, _k in
                               arcs.select('*', j) + arcs.select(j, '*')) == s)

        sums.append(s)

    vars = []
    for x in sums:
        flag = gpm.addVar(vtype=GRB.BINARY, name="temp")

        gpm.addConstr(x >= flag)
        gpm.addConstr(x <= 10000*flag)

        vars.append(flag)

    gpm.addConstr(quicksum(vars) <= 1)


# Compute optimal solution
gpm.optimize()

# Print solution
if gpm.status == GRB.Status.OPTIMAL:
    paths = set()
    p_set = set()

    solution = gpm.getAttr('x', flow)
    for h in commodities:
        for i, j in arcs:
            if solution[h, i, j] > 0.001:
                paths.add((i, j))
                p_set.add((int(i) % m, int(i) // m))
                p_set.add((int(j) % m, int(j) // m))

    all_plot = []

    for y in range(n):
        for x in range(m):
            if (x, y) in p_set:
                all_plot.append((x, y))

    plt.scatter([x[0] for x in all_plot], [x[1] for x in all_plot])

    for x in paths:
        x, y = x

        sx = int(x) % m
        sy = int(x) // m
        ex = int(y) % m
        ey = int(y) // m

        plt.annotate("",
                     xy=(sx, sy), xycoords='data',
                     xytext=(ex, ey), textcoords='data',
                     arrowprops=dict(arrowstyle="->",
                                     connectionstyle="arc3"))

    plt.show()
