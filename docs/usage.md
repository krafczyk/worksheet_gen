# Worksheet Generators

Run the scripts with Python and ReportLab installed (the existing environment is
`worksheet_venv/bin/python`). Each command writes a PDF to `--output`, replacing
that file if it already exists.

| Script | Default operations | Inclusive operand range | Default output |
| --- | --- | --- | --- |
| `mad_minute.py` | `+`, `-`, `x`, equally likely | 1-9 | `mad_minute.pdf` |
| `mad_minute_add.py` | `+` | 1-9 | `mad_minute_add.pdf` |
| `mad_minute_addsub.py` | `+`, `-`, equally likely | 1-19 | `mad_minute_addsub.pdf` |
| `mad_minute_mult.py` | `x` | 1-6 | `mad_minute_mult.pdf` |

## Operation Distribution

All four scripts accept `--operations` as a quoted Python literal list. Use the
operator strings `+`, `-`, and `x`. Bare operations have weight 1; optionally
include `(operation, weight)` tuples, including in a list with bare operations.
The option replaces the script's default operation distribution.

```sh
worksheet_venv/bin/python mad_minute.py --operations "['+', '-', 'x']"
worksheet_venv/bin/python mad_minute.py --operations "[('+', 3), ('-', 1)]" --pages 2
worksheet_venv/bin/python mad_minute_add.py --operations "['+', ('x', 2)]" --maximum 12
```

Weights are relative probabilities, not exact quotas: weights 3 and 1 mean a
75% and 25% chance per problem. Repeated operators contribute additional weight.
Zero weights disable entries. The list must not be empty, weights must be finite
non-negative numbers, and their total must be finite and positive. Invalid
distributions are rejected before writing a PDF. The literal is parsed as data,
not executed as Python code.

Both displayed operands remain within `--minimum` and `--maximum`. Subtraction
always has a non-negative result, with its second operand sampled between the
minimum and its first operand.

## Other Options

All scripts accept `--output`, `--minimum`, `--maximum`, `--rows` (default 8),
`--cols` (default 5), `--font-size` (default 20), and `--pages` (default 1).
Use `--help` for the command-line reference.

## Python API

```python
from worksheet import sample_problems

problems = sample_problems(
    40,
    minimum_operand=1,
    maximum_operand=9,
    operations=['+', ('-', 3), 'x'],
)
```

`sample_problems` defaults to equally likely addition, subtraction, and
multiplication. It returns a list of `Problem` objects and raises `ValueError`
for negative counts, invalid operand ranges, or invalid distributions. A count
of zero returns an empty list after validating the inputs. Sampling uses
Python's global `random` generator. The existing operation-specific sampling
functions remain available and delegate to this shared sampler.

Run the tests with:

```sh
worksheet_venv/bin/python -B -m unittest discover -s tests -v
```
