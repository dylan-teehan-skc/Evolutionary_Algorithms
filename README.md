# Evolutionary Algorithms

A from-scratch evolutionary algorithm system in Python with two modes:

- **GA (genetic algorithm):** evolves fixed-length bitstrings. Currently solves OneMax (maximise the number of 1s).
- **GP (genetic programming):** evolves expression trees for symbolic regression, finding a formula that fits a set of `(x, y)` points.

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
  fitness.py          OneMax (GA), negative absolute error (GP)
  tree.py             Tree helpers: function/terminal sets, random trees, grafting, printing
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
| `target_fitness.ga` / `target_fitness.gp` | Stop early once the best fitness reaches this value |
| `points` | GP: the `[x, y]` data points to fit |

Selection methods with settings read them from a block named after the method, such as `selection.tournament`. To add a new selection method, write it in `src/selection.py`, register it in `SELECTIONS` in `src/runner.py`, and set `selection.method` in the config.

The GP function set (`+`, `-`, `*`) and terminal set (`x`, `1.0`) are defined at the top of `src/tree.py`.

## Output

The run first prints the seed it used. Then each generation prints one line: the generation number and the best fitness in the population.

```
Seed: 42
0 -480
1 -480
2 0.0
```

When the run finishes, by reaching the target fitness or the last generation, it prints the best individual and its fitness:

```
Best: (((1.0 + (x * x)) * (x * (1.0 + x))) * 1.0)
Fitness: 0.0
```

This is the exact output of the default `config.yaml` (GP, seed 42).

How to read the fitness:

- **GA:** the number of 1s in the bitstring. Higher is better, and the maximum equals `length`.
- **GP:** the negative sum of absolute errors over all `points`. Higher is better, and `0` is a perfect fit. The best individual is printed as an infix expression. It's often not simplified, so the example above is `x⁴ + x³ + x² + x` written in an expanded form.

## Reproducing results

Every run is seeded from `seed` in `config.yaml`, and the seed is printed at the start of the output. To reproduce a run, use the same `config.yaml` with the same `seed`, and run `uv run main.py` with the dependency versions pinned in `uv.lock`. The output will match line for line.

The seed works because every operator draws from Python's global `random` module, which `src/runner.py` seeds once before the run starts. Any new operator must use `random` too (not NumPy or `random.Random()` instances) or runs stop being reproducible.

### Repeated runs

```bash
uv run experiment.py
```

This runs the current `config.yaml` once per seed, using seeds `seed`, `seed + 1`, ..., `seed + runs - 1` (42 to 71 by default). It prints a summary and writes two CSV files to `results/`, named after the algorithm and selection method:

| File | Contents |
|---|---|
| `<algorithm>_<selection>.csv` | One row per run: seed, final best fitness, generations used, whether the target was reached, best individual |
| `<algorithm>_<selection>_convergence.csv` | One row per run per generation: seed, generation, best fitness so far (the convergence curve) |

Summary statistics are taken over each run's final best fitness:

- `best`, `worst`, `mean`, `median` and `stdev`
- `success_rate`: the fraction of runs that reached `target_fitness`
- `mean_evals_to_target`: the average number of fitness evaluations successful runs needed, counting generation 0 as one population's worth

To compare configurations, change `config.yaml` (for example `selection.method`) and run it again. Each configuration writes to its own file.
