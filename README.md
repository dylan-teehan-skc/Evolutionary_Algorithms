# Evolutionary Algorithms

A from-scratch evolutionary algorithm system in Python with two modes:

- **GA (genetic algorithm):** evolves fixed-length bitstrings. Currently solves OneMax (maximise the number of 1s).
- **GP (genetic programming):** evolves expression trees for symbolic regression, finding a formula that fits a set of `(x, y)` points.

Both modes share the same evolution loop and selection operators. Only the representation-specific operators (initialisation, crossover, mutation, fitness) change. No EA frameworks are used. Every EA component is written by us.

## Project structure

```
main.py               Entry point: loads config.yaml and calls the runner
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

Each generation prints one line: the generation number and the best fitness in the population.

```
0 -425.0
1 -30.0
2 -30.0
...
```

When the run finishes, by reaching the target fitness or the last generation, it prints the best individual and its fitness:

```
Best: ((1.0 + x) * (((x * x) * (1.0 * x)) + ((x + 1.0) - 1.0)))
Fitness: 0.0
```

How to read the fitness:

- **GA:** the number of 1s in the bitstring. Higher is better, and the maximum equals `length`.
- **GP:** the negative sum of absolute errors over all `points`. Higher is better, and `0` is a perfect fit. The best individual is printed as an infix expression. It's often not simplified, so the example above is `x⁴ + x³ + x² + x` written in an expanded form.

## Reproducing results

Runs are currently **not seeded**, so each run gives different results. Seeding, repeated runs and benchmark scripts are still to be added. This section will document them once they exist.
