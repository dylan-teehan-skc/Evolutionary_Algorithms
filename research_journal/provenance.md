# What does our basic GA algorithm have and how do we refactor it to be suitable for GP:

Initially I created GA.py which does everything, when expanding this code so it's suitable for extension we have to think about how we actually structure this code so we can reuse necessary parts and that we can maintain this codebase for both our GA and GP code. 

Following SOLID principles we split each stage up into its own associated file, creating main.py that serves only as the entry. 

The main generic parts of any evolutionary algorithm are:

- Initialisation
- Selection
- Eliteism
- Crossover
- Mutation
- Calculating fitness
- The evolution loop

Breaking it down into these digestible parts, we then planned our codebase structure to align with this abstraction

I then looked at what the differences between GA and GP are:

| Stage | GA | GP |
|---|---|---|
| Initialisation | A population of random fixed-length arrays of bits. | Ramped half-and-half. Half full (every branch reaches max depth), half grow (branches can stop early). |
| Selection | Tournament. Pick k at random and the fittest becomes a parent. | Tournament, same as GA. |
| Elitism | Copy the best few unchanged into the next generation. | Same as GA. |
| Crossover | Pick a cut point and swap the segments between the two parents. | Pick a random node in each parent and swap the subtrees below them. |
| Mutation | Flip a bit or nudge a value at a random position. | Pick a node and replace its subtree with a newly grown random subtree. |
| Calculating fitness | Decode the array and score it with the objective function. | Run the tree on the data and measure the error against the targets. |
| The evolution loop | Evaluate → select → crossover → mutate → repeat. Evolves the best set of parameters for a problem whose structure is already fixed. | Same loop as GA. Evolves programs or expressions and finds the structure itself. Representation is a tree: function set (+, −…) for internal nodes, terminal set (x, constants) for leaves. |
| Constraints | Fixed length. | Leaves must be terminals, and there’s a max tree depth. |
| Output | A solution vector. | An executable program or expression. |

Updates required to go from GA to GP:

loads config.yaml crossover rate, mutation rate, max_tree_depth - using python dependancy manager uv - representation of population - initialize - half and half (grow and full) - ensure leaf nodes are not function nodes and are (function set and terminal set) - crossover you need to pick a node - mutation should be able to grow a tree to a single depth - ensure leaf nodes aren't function sets - fitness evaluation 

Pick a particular data structure you want to use (tree based)

https://gatree.readthedocs.io/en/latest/
Selection: Use tournament by default
