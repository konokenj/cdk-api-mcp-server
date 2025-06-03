# CDK API MCP Server

[![PyPI - Version](https://img.shields.io/pypi/v/konokenj.cdk-api-mcp-server.svg)](https://pypi.org/project/konokenj.cdk-api-mcp-server)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/konokenj.cdk-api-mcp-server.svg)](https://pypi.org/project/konokenj.cdk-api-mcp-server)

---

## Usage

Add to your mcp.json:

```json
{
  "mcpServers": {
    "konokenj.cdk-api-mcp-server": {
      "command": "uvx",
      "args": ["konokenj.cdk-api-mcp-server@latest"]
    }
  }
}
```

## MCP Server Capabilities

### Resource: CDK API packages

Registered as static resources. To get available modules under the package, call `list_resources()` as MCP client.

- `cdk-api-docs://constructs/@aws-cdk` ... Alpha modules published in `@aws-cdk` namespace
- `cdk-api-docs://constructs/aws-cdk-lib` ... Stable modules in `aws-cdk-lib` package

### Resource Template: List modules in package

To get available documents under the module, call `read_resource(uri)` as MCP client.

> [!Note]
> Chagne first and second part of uri as you need.

- `cdk-api-docs://constructs/@aws-cdk/{module}/`
- `cdk-api-docs://constructs/aws-cdk-lib/{module}/`

### Resource Template: Read file contents

To read a document, call `read_resource(uri)` as MCP client.

- `cdk-api-docs://constructs/@aws-cdk/{module}/{file}`
- `cdk-api-docs://constructs/aws-cdk-lib/{module}/{file}`

## License

Distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
