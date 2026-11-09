# Evolutionary Algorithms

A from-scratch evolutionary algorithm system in Python with two modes:

- **GA (genetic algorithm):** evolves fixed-length bitstrings. Currently solves OneMax (maximise the number of 1s).
- **GP (genetic programming):** evolves expression trees for symbolic regression, finding a formula that fits a set of `(x, y)` points. It's benchmarked on four problems from the Nguyen suite (Uy et al. 2011).

Both modes share the same evolution loop and selection operators. Only the representation-specific operators (initialisation, crossover, mutation, fitness) change. No EA frameworks are used. Every EA component is written by us.

## Project structure

```
main.py               Entry point: one run of config.yaml
experiment.py         Repeated runs over many seeds, with summary stats and CSV output
config.yaml           All run settings (algorithm, operators, parameters, data)
src/
  runner.py           Picks the operators for GA or GP and starts the run
  evolution.py        The generic evolution loop (evaluate, select, breed, repeat)
  initialisation.py   Random bitstrings (GA), ramped half-and-half (GP)
  selection.py        Tournament and roulette selection
  crossover.py        One-point (GA), subtree (GP)
  mutation.py         Bit-flip (GA), grow-by-one-level (GP)
  fitness.py          OneMax (GA), negative absolute error and the hit-based success check (GP)
  tree.py             Tree helpers: function/terminal sets, random trees, grafting, printing
  benchmarks.py       The Nguyen benchmark problems and their training points
design_docs/figures/  Architecture and flow diagrams
research_journal/     Research and design journal
```

## Dependencies

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.12 or newer (developed on 3.13.7) | Language |
| [uv](https://docs.astral.sh/uv/) | 0.9 or newer | Dependency and environment manager |
| [PyYAML](https://pyyaml.org/) | 6.0.3 | Reading `config.yaml` |
| [treelib](https://treelib.readthedocs.io/en/latest/) | 1.8.0 | Tree data structure for GP genomes |
| [black](https://black.readthedocs.io/) (dev only) | 26.10.1 | Code formatting |

Exact versions are pinned in `uv.lock`.

## Install

1. Install uv by following the [official instructions](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone the repository and install the dependencies:

```bash
git clone https://github.com/dylan-teehan-skc/Evolutionary_Algorithms.git
cd Evolutionary_Algorithms
uv sync
```

`uv sync` creates a `.venv` and installs the exact versions from `uv.lock`. If Python 3.12 or newer isn't installed, uv downloads it.

## Run

```bash
uv run main.py
```

## Configure

Run settings live in `config.yaml`:

| Key | Meaning |
|---|---|
| `algorithm` | `ga` or `gp` |
| `seed` | Random seed. The same seed and config always give the same run |
| `runs` | Number of seeds `experiment.py` runs, starting from `seed` |
| `initialisation.bitstrings.length` | GA: number of bits per individual |
| `initialisation.trees.max_tree_depth` | GP: maximum tree depth, used by initialisation, crossover and mutation |
| `selection.method` | `tournament` or `roulette` |
| `selection.tournament.tournament_size` | Number of individuals competing in each tournament |
| `evolution.population_size` | Individuals per generation |
| `evolution.generations` | Maximum number of generations |
| `evolution.crossover_rate` | Probability that a pair of parents is crossed over |
| `evolution.mutation_rate` | Probability that each child is mutated |
| `evolution.elites` | Number of best individuals copied unchanged into the next generation |
| `problem` | GP benchmark: `nguyen-1`, `nguyen-2`, `nguyen-5` or `nguyen-7` |
| `success.ga` | GA: a run succeeds, and stops early, once the best fitness reaches this |
| `success.gp` | GP: a run succeeds, and stops early, once every point's absolute error is below this (a "hit" on every point) |

Selection methods with settings read them from a block named after the method, such as `selection.tournament`. To add a new selection method, write it in `src/selection.py`, register it in `SELECTIONS` in `src/runner.py`, and set `selection.method` in the config.

### GP benchmarks

The four problems come from the Nguyen symbolic regression suite as defined by Uy et al. (2011). Each one trains on 20 points sampled uniformly from its range. The points come from a fixed data seed, so every run and every configuration sees the same data.

| Problem | Target function | Range |
|---|---|---|
| `nguyen-1` | x³ + x² + x | [-1, 1] |
| `nguyen-2` | x⁴ + x³ + x² + x (Koza's quartic, Koza 1992) | [-1, 1] |
| `nguyen-5` | sin(x²)·cos(x) − 1 | [-1, 1] |
| `nguyen-7` | log(x + 1) + log(x² + 1) | [0, 2] |

The function set is `+ - * / sin cos exp log` and the terminal set is `x`, matching the published setup. They're defined in one table, `PRIMITIVES`, at the top of `src/tree.py`. Division and log are protected so every tree can be evaluated: `x / 0` returns 1 and `log(x)` is computed as `log|x|`, with `log(0)` = 0. A tree that overflows or produces a non-finite value gets a capped worst-case error.

## Output

The run first prints the seed it used. Then each generation prints one line: the generation number and the best fitness in the population.

```
Seed: 42
0 -2.731479989649432
1 -1.4174223287997048
2 -1.4174223287997048
3 -1.4174223287997048
4 -2.7755575615628914e-16
```

When the run finishes, by succeeding or reaching the last generation, it prints the best individual and its fitness:

```
Best: (((x * x) * x) + ((x * x) + x))
Fitness: -2.7755575615628914e-16
```

This is the exact output of the default `config.yaml` (GP on Nguyen-1, seed 42).

How to read the fitness:

- **GA:** the number of 1s in the bitstring. Higher is better, and the maximum equals `length`.
- **GP:** the negative sum of absolute errors over the 20 training points. Higher is better, and `0` is a perfect fit. Tiny values like `-2.8e-16` are floating-point rounding, so the fit above is exact: the printed expression is `x³ + x² + x`. Expressions are printed in infix form and aren't simplified.

## Reproducing results

Every run is seeded from `seed` in `config.yaml`, and the seed is printed at the start of the output. To reproduce a run, use the same `config.yaml` with the same `seed`, and run `uv run main.py` with the dependency versions pinned in `uv.lock`. The output will match line for line.

The seed works because every operator draws from Python's global `random` module, which `src/runner.py` seeds once before the run starts. Any new operator must use `random` too (not NumPy or its own `random.Random()`) or runs stop being reproducible. The one deliberate exception is `src/benchmarks.py`, which samples training points with its own fixed generator so the data never changes with the run seed.

### Repeated runs

```bash
uv run experiment.py
```

This runs the current `config.yaml` once per seed, using seeds `seed`, `seed + 1`, ..., `seed + runs - 1` (42 to 71 by default). It prints a summary and writes two CSV files to `results/`, named after the algorithm and selection method:

| File | Contents |
|---|---|
| `<algorithm>_<selection>[_<problem>].csv` | One row per run: seed, final best fitness, generations used, whether the run succeeded, best individual |
| `<algorithm>_<selection>[_<problem>]_convergence.csv` | One row per run per generation: seed, generation, best fitness so far (the convergence curve) |

GP file names include the problem, for example `gp_tournament_nguyen-5.csv`. `results/` is ignored by git, because any result can be regenerated from the config and seeds.

Summary statistics are taken over each run's final best fitness:

- `best`, `worst`, `mean`, `median` and `stdev`
- `success_rate`: the fraction of runs that met the `success` rule
- `mean_evals_to_target`: the average number of fitness evaluations successful runs needed, counting generation 0 as one population's worth

To compare configurations, change `config.yaml` (for example `selection.method`) and run it again. Each configuration writes to its own file.
