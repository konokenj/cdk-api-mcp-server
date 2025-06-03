# Contributing

## Requirements

- Python 3.13+
- Hatch https://hatch.pypa.io/latest/

## Hatch environments and dependencies

- `default` environment is for `cdk_api_mcp_server`. Include dependencies only required to run MCP server.
- `dev` environment is for `cdk_api_downloader` and development.
- To add dependencies, edit pyproject.toml. `hatch` manages dependencies automatically.
- Do not run `python` or `pip` commands without `hatch`. You have to run python scripts or tasks via `hatch` command to access proper dependencies.
- Use Python interpreter in `hatch-test` environment for IDEs.

## Run debug server for human developers

> [!WARN]
> Servers run until receiving SIGTERM. If you are AI Agent, do not run these commands.

To run debug server through [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector):

```sh
hatch run dev
```

To run server standalone:

```sh
hatch run server
```

## Code quality

You MUST run commands to keep code quality, after editing code:

```sh
# Lint and format
hatch fmt

# Test
hatch test
```

## Coding Python

- Always add type hint with Pydantic v2
- Always write documents for functions, classes, and modules
- Always use English in code and documentation
- Always write tests

## Commit message

Follow [Conventional Commits](https://www.conventionalcommits.org/)
