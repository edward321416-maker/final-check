# Actual captures

`baseline/C01.json` through `baseline/C08.json` are the primary unchanged-extractor
outputs and actual gated profiles. `baseline/execution.json` records chronology,
freeze commit and output hashes. Manual scoring refers only to these files.

The C01-C08 files at this directory's top level record the earlier post-freeze
harness failure: Pydantic objects could not be JSON serialized. They contain no
saved candidates and are **UNSCORED HARNESS ERRORS**, not extractor benchmark
failures. They are preserved for honesty and excluded from every primary metric.
The wrapper serialization was repaired; Gold and product code were unchanged.
