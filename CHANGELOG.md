# CHANGELOG

<!-- version list -->

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

- Add --test-with-mocks cli param and check local rpc function
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
