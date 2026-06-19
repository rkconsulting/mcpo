# TODO: Hidden Tools Feature

## Phase 1: Core Implementation
- [x] Add `hiddenTools`/`hidden_tools` validation in `validate_server_config()`
- [x] Store `hidden_tools` state in `create_sub_app()`
- [x] Pass `include_in_schema=False` for hidden tools in `create_dynamic_endpoints()`
- [x] Add unit tests for validation (valid, invalid, snake_case)
- [x] Update README.md with documentation and examples
- [x] Add OWUI naming caveat to documentation
- [x] Create STRUCTURE.md

## Phase 2: Verification
- [x] Run unit tests (31 passed)
- [ ] Manual integration test with live MCP server

## Future Improvements
- Consider adding CLI flag `--hidden-tools` for single-server mode
- Add integration test verifying hidden tool is callable but absent from OpenAPI schema
