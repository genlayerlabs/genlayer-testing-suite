# CHANGELOG

<!-- version list -->

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
