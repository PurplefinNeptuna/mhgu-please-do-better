# Tests

`./build.sh test --host` runs `core/tests/behavior.rs`: attribution, quantity bounds, the INI
format and production persistence against a recording filesystem, hook publication and rollback,
the kernel platform and its trampoline relocation, and the publication primitives.

The full `./build.sh test` adds seven Unicorn probes in `scripts/` that execute the compiled plugin
and copied game code. None of them is gameplay evidence.
