# blogspot-publishing

Utility to publish a blog to Blogspot.

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and running Python tools.

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

Install dependencies:

```bash
make install
```

Or using uv directly:

```bash
uv sync
```

## Development

### Project Structure

```
blogspot-publishing/
├── src/
│   └── blogspot_publishing/    # Main package source code
├── tests/                      # Test files
├── pyproject.toml             # Project configuration
├── uv.lock                    # Locked dependencies
├── Makefile                   # Build automation
└── README.md                  # This file
```

### Available Commands

Run `make help` to see all available commands:

```bash
make help              # Show all available commands
make install           # Install dependencies
make format            # Format code with ruff
make lint              # Lint code with ruff
make lint-fix          # Fix linting issues automatically
make test              # Run tests with pytest
make test-verbose      # Run tests with verbose output
make coverage          # Run tests with coverage report
make check             # Run all checks (format, lint, test)
make clean             # Clean build artifacts
```

### Running Commands

All commands can be run with `make`:

```bash
# Install dependencies
make install

# Format code
make format

# Lint code
make lint

# Run tests
make test

# Run all checks
make check
```

Or using uv directly:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Run tests
uv run pytest
```

## Testing

Tests are located in the `tests/` directory and use pytest:

```bash
make test
```

## Code Quality

This project uses:

- **ruff** - For linting and formatting Python code
- **pytest** - For running tests

## License

See [LICENSE](LICENSE) file for details.
