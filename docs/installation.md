# Stable release
## As a CLI utility

If you're interested in utilizing bonfo's CLI interface you can install it a couple ways to make it available to your user.

Using **pipx** or **pip**:
=== "pipx"
    ``` bash
    $ pipx install bonfo
    $ bonfo
    ```

=== "pip"
    ``` bash
    $ pip install --user bonfo
    $ bonfo
    ```

## As a python module
Run one of these commands in your terminal:

=== "poetry"

    ``` bash
    $ poetry install bonfo
    ```

=== "pip"

    ``` bash
    $ pip install bonfo
    ```

This is the preferred method to install Bonfo, as it will always install the most recent stable release.

If you don't have [pip][] installed, this [Python installation guide][]
can guide you through the process.

For [Poetry][], follow their [installation guide][].

# From source

The source for Bonfo can be downloaded from
the [Github repo][].

You can either clone the public repository:

``` bash
$ git clone git://github.com/destos/bonfo
```

Or download the [tarball][]:

``` bash
$ curl -OJL https://github.com/destos/bonfo/tarball/main
```

Once you have a copy of the source, you can install it with pip or poetry while inside the Bonfo source directory:

=== "poetry"

    ``` bash
    $ poetry install
    ```

=== "pip"

    ``` bash
    $ pip install .
    ```

[pip]: https://pip.pypa.io
[Python installation guide]: http://docs.python-guide.org/en/latest/starting/installation/
[Github repo]: https://github.com/destos/bonfo
[tarball]: https://github.com/destos/bonfo/tarball/main
[Poetry]: https://python-poetry.org/
[installation guide]: https://python-poetry.org/docs/#installation
