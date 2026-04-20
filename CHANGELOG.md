# CHANGELOG

<!-- version list -->

## v0.29.1 (2026-04-20)

### Bug Fixes

- **gltest**: Bump genlayer-py to >=0.12.1 for Bradbury RPC fix
  ([#75](https://github.com/genlayerlabs/genlayer-testing-suite/pull/75),
  [`08c9d60`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/08c9d60f30d1a1afbed2214f39492be352a20a8b))


## v0.29.0 (2026-04-20)

### Bug Fixes

- **gltest**: Address CodeRabbit feedback for testnet_bradbury
  ([#74](https://github.com/genlayerlabs/genlayer-testing-suite/pull/74),
  [`b1b9596`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/b1b9596db76fd49d2b86687dc4e95c19d8e81045))

### Features

- **gltest**: Add testnet_bradbury to preconfigured networks
  ([#74](https://github.com/genlayerlabs/genlayer-testing-suite/pull/74),
  [`b1b9596`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/b1b9596db76fd49d2b86687dc4e95c19d8e81045))


## v0.28.0 (2026-03-30)

### Features

- **gltest**: Add appeal support to Contract class
  ([#72](https://github.com/genlayerlabs/genlayer-testing-suite/pull/72),
  [`c20cd3e`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/c20cd3e00ec616fcd2c929a75f67d9138e391ca0))


## v0.27.3 (2026-03-27)

### Bug Fixes

- **ci**: Git add sibling file in docs sync
  ([`1cc3f41`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/1cc3f41ecae8fae2f7b5115d66d5fdaa03413bf2))


## v0.27.2 (2026-03-27)

### Bug Fixes

- **ci**: Use sibling file pattern for docs sync
  ([`6fd22b6`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/6fd22b611904783a41f947bb73329ccbedf2dc07))


## v0.27.1 (2026-03-27)

### Bug Fixes

- **docs**: Strip badges and emojis from README when syncing to docs
  ([`46c750f`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/46c750f6eb93cc51bf70eb5d9fa345d6d21df38b))


## v0.27.0 (2026-03-27)

### Features

- **docs**: Param tables, README as index, _meta.json in sync
  ([`c9cf186`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/c9cf18626158946daca83371c657f086fcd58465))


## v0.26.0 (2026-03-27)

### Features

- Add API reference generation and docs sync
  ([`525178f`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/525178f2f698d0e5b288a623614d38162e92fe3b))


## v0.25.0 (2026-03-11)

### Features

- **direct**: Add lazy-api compat for eq_principle.strict_eq
  ([`b39f8ea`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/b39f8ea615676bdc392567f07740b8d8526756e4))


## v0.24.0 (2026-03-03)

### Features

- **direct**: Enforce cross-contract call restriction inside nondet context
  ([`475966e`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/475966e46c42652de71f7249bbcd534a1223f6c2))


## v0.23.0 (2026-02-25)

### Features

- **direct**: Add calldata roundtrip for constructor and method args
  ([`2ff9d07`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/2ff9d077b38329b0626d32cfd5d0b4080d071c03))

- **glsim**: Add sim_getMocks handler, strict mock mode, VecDB fix
  ([`5dc39cf`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/5dc39cf5cac17c16745d61c5d23a55654184e478))


## v0.22.0 (2026-02-23)

### Bug Fixes

- **glsim**: Add eth_getBlockByNumber for wallet compatibility
  ([#62](https://github.com/genlayerlabs/genlayer-testing-suite/pull/62),
  [`64e9a11`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/64e9a1105e361e21b4a61d5ff98502f86dc1d9e3))

### Chores

- Resolve uv.lock conflict from stash
  ([#62](https://github.com/genlayerlabs/genlayer-testing-suite/pull/62),
  [`64e9a11`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/64e9a1105e361e21b4a61d5ff98502f86dc1d9e3))

### Features

- Cloudpickle bypass, gl.message sync, persistent mocks, random seed
  ([#62](https://github.com/genlayerlabs/genlayer-testing-suite/pull/62),
  [`64e9a11`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/64e9a1105e361e21b4a61d5ff98502f86dc1d9e3))

- **glsim**: Add Anvil-style time manipulation RPC methods
  ([#62](https://github.com/genlayerlabs/genlayer-testing-suite/pull/62),
  [`64e9a11`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/64e9a1105e361e21b4a61d5ff98502f86dc1d9e3))

- **glsim**: Sdk compat, consensus, time manipulation, and eth_getBlockByNumber
  ([#62](https://github.com/genlayerlabs/genlayer-testing-suite/pull/62),
  [`64e9a11`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/64e9a1105e361e21b4a61d5ff98502f86dc1d9e3))


## v0.21.0 (2026-02-23)

### Bug Fixes

- **deps**: Remove setuptools from runtime dependencies
  ([#63](https://github.com/genlayerlabs/genlayer-testing-suite/pull/63),
  [`1349dfa`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/1349dfad60291832eb84e7af7dacbf0a6a36a1b6))

- **docs**: Use uv run for all gltest commands in CLAUDE.md
  ([#63](https://github.com/genlayerlabs/genlayer-testing-suite/pull/63),
  [`1349dfa`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/1349dfad60291832eb84e7af7dacbf0a6a36a1b6))

### Chores

- Migrate CI and build pipeline to uv
  ([#63](https://github.com/genlayerlabs/genlayer-testing-suite/pull/63),
  [`1349dfa`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/1349dfad60291832eb84e7af7dacbf0a6a36a1b6))

### Documentation

- Update dev commands to use uv
  ([#63](https://github.com/genlayerlabs/genlayer-testing-suite/pull/63),
  [`1349dfa`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/1349dfad60291832eb84e7af7dacbf0a6a36a1b6))

### Features

- **ci**: Migrate build, test, and publish pipelines to uv
  ([#63](https://github.com/genlayerlabs/genlayer-testing-suite/pull/63),
  [`1349dfa`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/1349dfad60291832eb84e7af7dacbf0a6a36a1b6))


## v0.20.4 (2026-02-19)

### Bug Fixes

- **glsim**: Add eth_getBlockByNumber for wallet compatibility
  ([#61](https://github.com/genlayerlabs/genlayer-testing-suite/pull/61),
  [`e4b68c3`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/e4b68c3659d5e6c912e7c9313f109919a2abd622))


## v0.20.3 (2026-02-19)

### Bug Fixes

- Rollback contract storage on failed transactions
  ([`a81c6a5`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/a81c6a56daf37ba190d1c8ca96102613a842eefd))


## v0.20.2 (2026-02-19)

### Bug Fixes

- Prevent unbounded PostMessage recursion with depth guard
  ([`5652787`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/5652787ab8303c9b5ab80a535e13e6749dd4ac87))


## v0.20.1 (2026-02-19)

### Bug Fixes

- Queue PostMessage calls instead of executing inline
  ([`9948af4`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/9948af4195a4cfea6b0c7c462fbb543fcb16cf94))


## v0.20.0 (2026-02-19)

### Bug Fixes

- Add _validUntil param to addTransaction test helper
  ([`7028461`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/702846175e5b3478d60ed6b4b252ec5d2c7fd317))

- Set gl.message context in call_method and deploy
  ([`99db612`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/99db6126de1114d7194a35c6b409b9f3270cc160))

### Documentation

- Restructure README around direct/studio testing modes
  ([`7110e2c`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/7110e2c69bbce8a8495b17be51129ee8e6c6486b))

### Features

- Add CORS middleware to glsim server
  ([`00b3088`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/00b30886ebd0cf00484ef5e13523b2d8f423d3d9))


## v0.19.2 (2026-02-10)

### Bug Fixes

- Use path-based module eviction in direct mode cleanup
  ([`68d72a1`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/68d72a19d3a47c3d519da4215e4da07832e5a8a3))

### Documentation

- Update project CLAUDE.md and direct-tests skill
  ([`9cf1605`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/9cf1605f024a9bf768a2f57275db33d404edb680))


## v0.19.1 (2026-02-09)

### Bug Fixes

- Add glsim version to semantic-release config
  ([`791a987`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/791a987b88b68dae912d6269a347e47479024811))


## v0.17.0 (2026-02-06)

### Features

- **direct**: Full snapshot/revert captures mocks, prank stack, sender, validators
- **direct**: Strict mocks mode (`vm.strict_mocks = True`) warns on unused mocks
- **direct**: MockNotFoundError now lists registered patterns for debugging

### Bug Fixes

- **direct**: `expect_revert` now properly handles `ContractRollback`, `ValueError`,
  `RuntimeError`, and generic exceptions with correct message matching

## v0.16.0 (2026-02-05)

### Features

- **direct**: Add `vm.check_pickling` for opt-in cloudpickle validation of run_nondet closures

### Bug Fixes

- **direct**: Fix falsy LLM mock responses (`""`, `0`, `{}`) rejected as missing mocks
- **direct**: Fix stale `gl.message` after `vm.value`, `vm.origin`, or `vm.warp()` mutations
- **direct**: Fix stdin fd leak — original stdin now restored on VM deactivation
- **direct**: Fix no-arg constructor skipped in fallback contract allocator
- **direct**: Always set unique contract address per deploy
- **direct**: Safe tar extraction with `filter='data'` (prevents path traversal)

## v0.15.0 (2026-02-05)

### Features

- **direct**: Add vm.run_validator() for testing nondet validator functions
  ([`bf5c9e1`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/bf5c9e1511b1c0e1134b13b7711e0d780e2fa862))


## v0.13.0 (2026-02-04)

### Features

- **direct**: Support RunNondet gl_call and fix web mock format
  ([`3405b16`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3405b169081800c3de9112495f669e74a336b452))


## v0.12.0 (2026-02-04)

### Bug Fixes

- Enable TreeMap tests by fixing address type handling
  ([`3ca6f2c`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3ca6f2cfd49f6f53494cf620c819f5611426909a))

### Features

- Add native Python test runner for GenLayer contracts
  ([`42f25bb`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/42f25bbb10c56022de4424df25798679c95da5bf))

### Performance Improvements

- Skip tarball parsing when SDK already extracted
  ([`4635446`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/46354463159d13767b7faa9cab09276c01fcf278))

### Refactoring

- Rename native → direct for clarity
  ([`6772215`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/6772215a8d3e2d41b4f8d25d187ce9e522a87919))


## v0.11.0 (2025-11-27)

### Documentation

- Replace yeagerai references with genlayerlabs
  ([#57](https://github.com/genlayerlabs/genlayer-testing-suite/pull/57),
  [`c22b9bc`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/c22b9bc5cd028d12baa292aeb375a24e2dd1b095))

- Update Discord invite links to current working link
  ([#57](https://github.com/genlayerlabs/genlayer-testing-suite/pull/57),
  [`c22b9bc`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/c22b9bc5cd028d12baa292aeb375a24e2dd1b095))

### Features

- Implement mock web request ([#53](https://github.com/genlayerlabs/genlayer-testing-suite/pull/53),
  [`bdb3a04`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/bdb3a04b13b6b953de98f1329d04368ebfafb783))

### Revert

- Keep original Discord link in CONTRIBUTING.md
  ([#57](https://github.com/genlayerlabs/genlayer-testing-suite/pull/57),
  [`c22b9bc`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/c22b9bc5cd028d12baa292aeb375a24e2dd1b095))


## v0.10.1 (2025-11-12)

### Bug Fixes

- Consider localnet in check_studio_based_rpc for leader-only mode
  ([#58](https://github.com/genlayerlabs/genlayer-testing-suite/pull/58),
  [`8f1d3cb`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/8f1d3cbcfa057b183cbe7b94ebd0c09c28cc3ccf))


## v0.10.0 (2025-11-11)

### Documentation

- Update README.md ([#56](https://github.com/genlayerlabs/genlayer-testing-suite/pull/56),
  [`64251ed`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/64251ed55476591561b1ff350dfb87a89ac0cea7))

### Features

- Deprecate setup_validators fixture and --test-with-mocks flag
  ([#54](https://github.com/genlayerlabs/genlayer-testing-suite/pull/54),
  [`29ea943`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/29ea943bede28be2b78915c738e188ca688d74ce))

- Deprecate setup_validators fixture and --test-with-mocks flag (DXP-650)
  ([#54](https://github.com/genlayerlabs/genlayer-testing-suite/pull/54),
  [`29ea943`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/29ea943bede28be2b78915c738e188ca688d74ce))

### Testing

- Remove deprecated test_with_mocks test cases
  ([#54](https://github.com/genlayerlabs/genlayer-testing-suite/pull/54),
  [`29ea943`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/29ea943bede28be2b78915c738e188ca688d74ce))

- Remove setup_validators from tests
  ([#54](https://github.com/genlayerlabs/genlayer-testing-suite/pull/54),
  [`29ea943`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/29ea943bede28be2b78915c738e188ca688d74ce))


## v0.9.0 (2025-09-11)

### Documentation

- New per network fields and chain CLI param
  ([#52](https://github.com/genlayerlabs/genlayer-testing-suite/pull/52),
  [`85d3323`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/85d3323a3ec895f9f9efabf98f78cb3517670069))

### Features

- Add chain to CLI ([#52](https://github.com/genlayerlabs/genlayer-testing-suite/pull/52),
  [`85d3323`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/85d3323a3ec895f9f9efabf98f78cb3517670069))

- Add more fields to manage in per network configuration (default wait retries, default wait
  intervals, test with mocks and chain)
  ([#52](https://github.com/genlayerlabs/genlayer-testing-suite/pull/52),
  [`85d3323`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/85d3323a3ec895f9f9efabf98f78cb3517670069))

- Remove limitation on custom network ids in code
  ([#52](https://github.com/genlayerlabs/genlayer-testing-suite/pull/52),
  [`85d3323`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/85d3323a3ec895f9f9efabf98f78cb3517670069))

### Performance Improvements

- Exclude directories from build
  ([#52](https://github.com/genlayerlabs/genlayer-testing-suite/pull/52),
  [`85d3323`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/85d3323a3ec895f9f9efabf98f78cb3517670069))

### Refactoring

- Chain to chain_type ([#52](https://github.com/genlayerlabs/genlayer-testing-suite/pull/52),
  [`85d3323`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/85d3323a3ec895f9f9efabf98f78cb3517670069))


## v0.8.0 (2025-09-10)

### Features

- Implement validator factory
  ([#49](https://github.com/genlayerlabs/genlayer-testing-suite/pull/49),
  [`56830f5`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/56830f54adc2558f4f2fc47218c405ca1051e32e))


## v0.7.0 (2025-09-09)

### Features

- Add consensus context field to transact and call methods, add genvm_datetime to analyze method
  ([#48](https://github.com/genlayerlabs/genlayer-testing-suite/pull/48),
  [`bcb3ab7`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/bcb3ab7a822d9d7109e577096e64016dac888caa))

- Virtual validators and custom genvm in transaction execution
  ([#48](https://github.com/genlayerlabs/genlayer-testing-suite/pull/48),
  [`bcb3ab7`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/bcb3ab7a822d9d7109e577096e64016dac888caa))

### Testing

- Custom genvm datetime ([#48](https://github.com/genlayerlabs/genlayer-testing-suite/pull/48),
  [`bcb3ab7`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/bcb3ab7a822d9d7109e577096e64016dac888caa))


## v0.6.0 (2025-08-01)

### Documentation

- Deploy_contract_tx and extract_contract_address methods
  ([#43](https://github.com/genlayerlabs/genlayer-testing-suite/pull/43),
  [`d10a233`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d10a2330bef1ab4cc769917306248b5d18e16b83))

### Features

- Implement deploy_contract_tx and extract_contract_address
  ([#43](https://github.com/genlayerlabs/genlayer-testing-suite/pull/43),
  [`d10a233`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d10a2330bef1ab4cc769917306248b5d18e16b83))

### Testing

- Invalid deploy ([#43](https://github.com/genlayerlabs/genlayer-testing-suite/pull/43),
  [`d10a233`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d10a2330bef1ab4cc769917306248b5d18e16b83))


## v0.5.1 (2025-07-31)

### Bug Fixes

- Filter problematic fields in tx receipt by default
  ([#41](https://github.com/genlayerlabs/genlayer-testing-suite/pull/41),
  [`e524a39`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/e524a3943893f17f5c4176b9e801b68944a0b93e))

- Triggered transactions is not in the response
  ([#41](https://github.com/genlayerlabs/genlayer-testing-suite/pull/41),
  [`e524a39`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/e524a3943893f17f5c4176b9e801b68944a0b93e))

### Chores

- Update genlayer-py to v0.8.1
  ([#41](https://github.com/genlayerlabs/genlayer-testing-suite/pull/41),
  [`e524a39`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/e524a3943893f17f5c4176b9e801b68944a0b93e))

### Refactoring

- Remove depecrated legacy contract examples
  ([#41](https://github.com/genlayerlabs/genlayer-testing-suite/pull/41),
  [`e524a39`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/e524a3943893f17f5c4176b9e801b68944a0b93e))

### Testing

- Update with latest tx status behavior
  ([#41](https://github.com/genlayerlabs/genlayer-testing-suite/pull/41),
  [`e524a39`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/e524a3943893f17f5c4176b9e801b68944a0b93e))


## v0.5.0 (2025-07-30)

### Bug Fixes

- Rollback to 0.4.1 and prevent major version updates
  ([#42](https://github.com/genlayerlabs/genlayer-testing-suite/pull/42),
  [`f59a3fe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/f59a3fe9a9af8f497b89c90df2037cb54c701d6a))

- Update default wait values ([#39](https://github.com/genlayerlabs/genlayer-testing-suite/pull/39),
  [`3c0e8ac`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3c0e8ac936a0ef3c96cbe3bd6f726792554a2521))

- Use default client as first option
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

- **gltest_cli**: Improve error handling
  ([#38](https://github.com/genlayerlabs/genlayer-testing-suite/pull/38),
  [`656410b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/656410be6bbaf0e3c389dc00e7578afd80e1285d))

### Chores

- Add ci bot to bypass branch protection
  ([#36](https://github.com/genlayerlabs/genlayer-testing-suite/pull/36),
  [`6322da0`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/6322da023554b96fcd2a4801d273c7e79d0d2908))

- Update genlayer-py to 0.7.1
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

- **deps**: Update genlayer-py version to v0.7.2
  ([#35](https://github.com/genlayerlabs/genlayer-testing-suite/pull/35),
  [`298c0be`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/298c0be4ff70844c3ffbdbeff1e3dcdcb221df7d))

### Documentation

- Added leader only and update project structure
  ([#34](https://github.com/genlayerlabs/genlayer-testing-suite/pull/34),
  [`07c0d94`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/07c0d94b478b37a9566e6512b02517fcd0db5e51))

- Mock llm responses ([#40](https://github.com/genlayerlabs/genlayer-testing-suite/pull/40),
  [`a3d947f`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/a3d947f0fa1d11d6f287b2dd2d5eb2a76a5289b3))

- Update network configuration
  ([#38](https://github.com/genlayerlabs/genlayer-testing-suite/pull/38),
  [`656410b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/656410be6bbaf0e3c389dc00e7578afd80e1285d))

- Update with breaking changes
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

### Features

- Add leader only as a cli param and network config
  ([#34](https://github.com/genlayerlabs/genlayer-testing-suite/pull/34),
  [`07c0d94`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/07c0d94b478b37a9566e6512b02517fcd0db5e51))

- Add leader only is now configurable outside tests
  ([#34](https://github.com/genlayerlabs/genlayer-testing-suite/pull/34),
  [`07c0d94`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/07c0d94b478b37a9566e6512b02517fcd0db5e51))

- Add studionet and testnet_asimov as pre configured networks
  ([#38](https://github.com/genlayerlabs/genlayer-testing-suite/pull/38),
  [`656410b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/656410be6bbaf0e3c389dc00e7578afd80e1285d))

- Handle pre defined networks (localnet, studionet, testnet_asimov)
  ([#38](https://github.com/genlayerlabs/genlayer-testing-suite/pull/38),
  [`656410b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/656410be6bbaf0e3c389dc00e7578afd80e1285d))

- Redesign method wrapper to handle different cases (call, transact, stats)
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

- Remove leader only param from transact and deploy methods
  ([#34](https://github.com/genlayerlabs/genlayer-testing-suite/pull/34),
  [`07c0d94`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/07c0d94b478b37a9566e6512b02517fcd0db5e51))

- Statistical prompt testing ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

- Update call, transact and deploy methods
  ([#39](https://github.com/genlayerlabs/genlayer-testing-suite/pull/39),
  [`3c0e8ac`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3c0e8ac936a0ef3c96cbe3bd6f726792554a2521))

- Update default behavior for tx status and triggered txs and align deploy method
  ([#39](https://github.com/genlayerlabs/genlayer-testing-suite/pull/39),
  [`3c0e8ac`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3c0e8ac936a0ef3c96cbe3bd6f726792554a2521))

- **cli**: Implement artifacts management
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

### Refactoring

- Delete glchain and improve modularity
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

### Testing

- Testnet asimov without configuration case
  ([#38](https://github.com/genlayerlabs/genlayer-testing-suite/pull/38),
  [`656410b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/656410be6bbaf0e3c389dc00e7578afd80e1285d))

- Update oracle factory ([#39](https://github.com/genlayerlabs/genlayer-testing-suite/pull/39),
  [`3c0e8ac`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3c0e8ac936a0ef3c96cbe3bd6f726792554a2521))

- Update test examples and add cli tests
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

- **gltest_cli**: Added plugin and integration tests
  ([#34](https://github.com/genlayerlabs/genlayer-testing-suite/pull/34),
  [`07c0d94`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/07c0d94b478b37a9566e6512b02517fcd0db5e51))


## v2.2.0 (2025-07-23)

### Bug Fixes

- **gltest_cli**: Improve error handling
  ([#38](https://github.com/genlayerlabs/genlayer-testing-suite/pull/38),
  [`656410b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/656410be6bbaf0e3c389dc00e7578afd80e1285d))

### Documentation

- Update network configuration
  ([#38](https://github.com/genlayerlabs/genlayer-testing-suite/pull/38),
  [`656410b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/656410be6bbaf0e3c389dc00e7578afd80e1285d))

### Features

- Add studionet and testnet_asimov as pre configured networks
  ([#38](https://github.com/genlayerlabs/genlayer-testing-suite/pull/38),
  [`656410b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/656410be6bbaf0e3c389dc00e7578afd80e1285d))

- Handle pre defined networks (localnet, studionet, testnet_asimov)
  ([#38](https://github.com/genlayerlabs/genlayer-testing-suite/pull/38),
  [`656410b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/656410be6bbaf0e3c389dc00e7578afd80e1285d))

### Testing

- Testnet asimov without configuration case
  ([#38](https://github.com/genlayerlabs/genlayer-testing-suite/pull/38),
  [`656410b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/656410be6bbaf0e3c389dc00e7578afd80e1285d))


## v2.1.0 (2025-07-22)

### Bug Fixes

- Update default wait values ([#39](https://github.com/genlayerlabs/genlayer-testing-suite/pull/39),
  [`3c0e8ac`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3c0e8ac936a0ef3c96cbe3bd6f726792554a2521))

### Features

- Update call, transact and deploy methods
  ([#39](https://github.com/genlayerlabs/genlayer-testing-suite/pull/39),
  [`3c0e8ac`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3c0e8ac936a0ef3c96cbe3bd6f726792554a2521))

- Update default behavior for tx status and triggered txs and align deploy method
  ([#39](https://github.com/genlayerlabs/genlayer-testing-suite/pull/39),
  [`3c0e8ac`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3c0e8ac936a0ef3c96cbe3bd6f726792554a2521))

### Testing

- Update oracle factory ([#39](https://github.com/genlayerlabs/genlayer-testing-suite/pull/39),
  [`3c0e8ac`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3c0e8ac936a0ef3c96cbe3bd6f726792554a2521))


## v2.0.0 (2025-07-21)

### Chores

- **deps**: Update genlayer-py version to v0.7.2
  ([#35](https://github.com/genlayerlabs/genlayer-testing-suite/pull/35),
  [`298c0be`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/298c0be4ff70844c3ffbdbeff1e3dcdcb221df7d))

### Documentation

- Added leader only and update project structure
  ([#34](https://github.com/genlayerlabs/genlayer-testing-suite/pull/34),
  [`07c0d94`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/07c0d94b478b37a9566e6512b02517fcd0db5e51))

### Features

- Add leader only as a cli param and network config
  ([#34](https://github.com/genlayerlabs/genlayer-testing-suite/pull/34),
  [`07c0d94`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/07c0d94b478b37a9566e6512b02517fcd0db5e51))

- Add leader only is now configurable outside tests
  ([#34](https://github.com/genlayerlabs/genlayer-testing-suite/pull/34),
  [`07c0d94`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/07c0d94b478b37a9566e6512b02517fcd0db5e51))

- Remove leader only param from transact and deploy methods
  ([#34](https://github.com/genlayerlabs/genlayer-testing-suite/pull/34),
  [`07c0d94`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/07c0d94b478b37a9566e6512b02517fcd0db5e51))

### Testing

- **gltest_cli**: Added plugin and integration tests
  ([#34](https://github.com/genlayerlabs/genlayer-testing-suite/pull/34),
  [`07c0d94`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/07c0d94b478b37a9566e6512b02517fcd0db5e51))


## v1.0.0 (2025-07-16)

### Bug Fixes

- Use default client as first option
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

### Chores

- Add ci bot to bypass branch protection
  ([#36](https://github.com/genlayerlabs/genlayer-testing-suite/pull/36),
  [`6322da0`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/6322da023554b96fcd2a4801d273c7e79d0d2908))

- Update genlayer-py to 0.7.1
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

### Documentation

- Update with breaking changes
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

### Features

- Redesign method wrapper to handle different cases (call, transact, stats)
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

- Statistical prompt testing ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

- **cli**: Implement artifacts management
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

### Refactoring

- Delete glchain and improve modularity
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))

### Testing

- Update test examples and add cli tests
  ([#32](https://github.com/genlayerlabs/genlayer-testing-suite/pull/32),
  [`d5b6cbe`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d5b6cbe1eb3b25715f90bd7cd3d9263c41bf5b79))


## v0.4.1 (2025-07-16)

### Bug Fixes

- Implement separated loggers for gltest and gltest cli
  ([`3ffd6bd`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/3ffd6bd92fbafdca70f10627d2b29e68159df4e8))


## v0.4.0 (2025-07-15)

### Documentation

- Added fixtures documentation
  ([#31](https://github.com/genlayerlabs/genlayer-testing-suite/pull/31),
  [`d80c88e`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d80c88ed5d3ac56dee32dba235015795306afd9b))

### Features

- Add --test-with-mocks cli param and check local rpc function (DEPRECATED)
  ([#31](https://github.com/genlayerlabs/genlayer-testing-suite/pull/31),
  [`d80c88e`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d80c88ed5d3ac56dee32dba235015795306afd9b))

- Added new fixtures ([#31](https://github.com/genlayerlabs/genlayer-testing-suite/pull/31),
  [`d80c88e`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d80c88ed5d3ac56dee32dba235015795306afd9b))

- Mock llm responses in tests
  ([#31](https://github.com/genlayerlabs/genlayer-testing-suite/pull/31),
  [`d80c88e`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d80c88ed5d3ac56dee32dba235015795306afd9b))

### Testing

- Update examples with genvm v0.1.3 syntax
  ([#31](https://github.com/genlayerlabs/genlayer-testing-suite/pull/31),
  [`d80c88e`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d80c88ed5d3ac56dee32dba235015795306afd9b))

- Update tests to use mocks and validator setup
  ([#31](https://github.com/genlayerlabs/genlayer-testing-suite/pull/31),
  [`d80c88e`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/d80c88ed5d3ac56dee32dba235015795306afd9b))


## v0.3.1 (2025-06-27)

### Bug Fixes

- Update genlayer-py 0.6.1
  ([`ff1d262`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/ff1d2620cf5da3dd3ea4ef3209950b3bdbcb6148))


## v0.3.0 (2025-06-25)

### Bug Fixes

- Exclude enviroment dirs from search
  ([`b136ffc`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/b136ffc9246e265c06014e8452e41b983f58b490))

### Continuous Integration

- Update test workflow
  ([`5ecbdcf`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/5ecbdcfee9096051641c07f6ddf68ec13b5b854e))

### Documentation

- Add gltest.config.yaml documentation
  ([`579ca0b`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/579ca0b1b78ee11561643fa9228a3dd546219e93))

### Features

- Add network param and move config logic to gltest_cli
  ([`c8f5fea`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/c8f5fea511e187c563bc357a2548ce8710868ffb))

- Implement gltest config file
  ([`ffc9aac`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/ffc9aac19e7555cd4ce399133746f3f3221822d4))

- Implement logging module
  ([`7d4b4a5`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/7d4b4a50a334dd3ba9e4ab2225938c16ee6dea0f))

- **testnet**: Add support for deploy and build contract functions
  ([`4bfd4c9`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/4bfd4c95fa41a499e70baf65b14a8b58ebeec4c3))

### Testing

- Increase coverage and organize folders
  ([`bf3052a`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/bf3052af17668a7da1bde34dce3631149365789a))


## v0.2.0 (2025-06-11)

### Bug Fixes

- Raise exception for duplicated contract names
  ([`558baad`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/558baadd508b39de22b74c5e86bda543a21e77dd))

### Continuous Integration

- Add automatic release
  ([`0038d99`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/0038d999aa1da522ee86faccf4b95298397a2cdc))

### Documentation

- Add changelog
  ([`002bf61`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/002bf61eaec4eba52766525fd022890691bbc87e))

- **contributing**: Added commit standards and versioning
  ([`06677d3`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/06677d3e2b4f7f951ba1280b80b6e6a8222d0f5f))

### Features

- Add new argument to find contract definition from file
  ([`ddf13c6`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/ddf13c663cead972e69ecd4adf9b75aef6198e05))

- Refactor duplicated logic and make contract_file_path to be relative to contracts dir
  ([`c811939`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/c811939fa1609f2881b056771d4ad38cc1f149de))

### Refactoring

- Update find_contract_definition name
  ([`9a59fc9`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/9a59fc9c845629dddfbe9759adc174c7f73d0dad))

### Testing

- Duplicate contract names
  ([`ecfbcb5`](https://github.com/genlayerlabs/genlayer-testing-suite/commit/ecfbcb56be13eb51d7d7ddbaa042ed83b56355cd))


## v0.1.3 (2025-06-05)

- Initial release
