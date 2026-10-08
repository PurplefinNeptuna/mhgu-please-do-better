# Please do Better r18-config2

READY_TO_DISTRIBUTE, locally packaged and unpublished. The INI now contains
only `force_miraculous=0` or `force_miraculous=1`, with a trailing newline.
Existing files beginning with `version=2` still load either preference value;
the next explicit Save settings removes that line. No automatic config writes
or backup access were added.

NRO SHA-256: `891802053b724dd3045d7fa1085a4409a88f801ccb4cb9ba06b32be14e883424`.
ZIP: `build/please-do-better/releases/r18-config2/please-do-better-r18-config2.zip`.

Host preference and production filesystem tests, 2,122 ARM checks, 100,511
compiled runtime/gateway checks and native/observation/display/highlight
fixtures passed. Imports and NZCVQ restoration were checked. Forcing, reward
highlights, hooks and UI are unchanged. [Config validation](docs/CONFIG_WITHOUT_VERSION.json)
records the tests and exact payload. Prior r17-config1 gameplay confirmation
remains in [RUNTIME.md](RUNTIME.md); no fresh game run is claimed for r18-config2.
Forge remains LOCAL_ONLY. Nothing was installed, activated or published.

The r17-config1 delivery is preserved with hashes under
`backups/config-no-version-20261008/`.
