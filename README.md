# Ferrit

![PyPI](https://img.shields.io/pypi/v/ferrit)

A stupid tool for listing and checking out Gerrit changes

## Getting started

### Installation

Install with pip
```
pip3 install --user ferrit
```
or from the repo
```
python3 setup.py install --user
```

### Configuration

There (currently) is none. Ferrit assumes that...
- You're using HTTP to talk to Gerrit
- The remote you want to use is `origin`
- Your HTTP credentials are stored in ~/.git-credentials
- You feel no desire to verify SSL certificates

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

Search for changes containing the words `foo` and `bar`
```
fe search foo bar
```

## Contributing

In the unlikely event that you want to contribute to Ferrit, please feel free to open a PR, open an issue, or email me.
