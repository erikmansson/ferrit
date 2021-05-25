# Ferrit

![PyPI](https://img.shields.io/pypi/v/ferrit)

A stupid tool for listing and checking out Gerrit changes

## Getting started

### Installation

Install from PyPI
```
pip install --user --upgrade ferrit
```
or from the repo
```
pip install .
```

### Configuration

There (currently) is none. Ferrit assumes that...
- You're using HTTP to talk to Gerrit
- The remote you want to use is `origin`

### Usage

Ferrit can be accessed both with the `ferrit` and `fe` command.

List relevant changes:
```
fe dashboard
```

Checkout the latest patch set of change 123:
```
fe checkout 123
```

Checkout patch set 45 of change 123:
```
fe checkout 123/45
```

In the same way as `checkout`, Ferrit also supports `fetch`, `cherry-pick`, `show` and `rev-parse` (printing the commit hash).

Search for changes containing the words `foo` and `bar`
```
fe search foo bar
```

## Contributing

In the unlikely event that you want to contribute to Ferrit, please feel free to open a PR, open an issue, or email me.
