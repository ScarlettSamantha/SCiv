# MyPy types for Kivy

This project includes some type stubs for [Kivy][], for use with [mypy][] and editors
that use mypy info to power autocomplete. This is partially driven by type
checking Kivy code, and partially because mypy is unable to understand Kivy
as a extension module, so warns on all Kivy imports otherwise, so using
mypy with a project that uses Kivy, even on non-Kivy code becomes noisy.

The types are currently far from complete, so PRs are welcome. 

## Usage

1. Checkout this repo.
2. Add to your mypy path.

via environment variable:

```sh
MYPYPATH=/path/to/mypy-types-kivy python3 -m mypy mymodule
```

or `mypy.ini`:

```ìni
[mypy]
mypy_path=/path/to/mypy-types-kivy
```


## Contributing

The canonical repo is on [tonyfinn/mypy-types-kivy][Gitlab] on gitlab, 
but PRs are also accepted to the [Github][Github] repo. Issues can also be 
reported to the [Issues][Gitlab-Issues] page.

### Useful Links

* [Kivy API docs][Kivy-API]
* [mypy docs][mypy-docs]


### Why not typeshed?

[Typeshed][] is a repo for hosting type stubs for third party libraries. This
project has not been submitted to Typeshed due to its incomplete nature. 
Library stubs in Typeshed require that they are blessed by the original
developers, and I'd rather wait until the stubs were much more complete before
seeking this. 


 [Gitlab]: https://gitlab.com/tonyfinn/mypy-types-kivy
 [Github]: https://github.com/tonyfinn/mypy-types-kivy
 [Gitlab-Issues]: https://gitlab.com/tonyfinn/mypy-types-kivy/issues
 [Kivy]: https://kivy.org
 [Kivy-API]: https://kivy.org/docs/api-kivy.html
 [mypy]: http://mypy-lang.org
 [mypy-docs]: https://mypy.readthedocs.io/en/latest/
