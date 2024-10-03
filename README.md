Your One Get Remaining Time library, in Python
==============================================

Python bindings to [libyogrt](https://github.com/LLNL/libyogrt), a library to efficiently query resource managers for the time remaining in a job.
This is useful for managing activities like checkpoint/restart, which you may want to do before a job allocation completes.

## Installation

You must install libyogrt yourself. (If you are on an LLNL system, it is probably already installed.)
Then:
```bash
# (clone PyYogrt)
cd pyyogrt
pip install .
```
(In the future, PyYogrt will be available in PyPI.)

PyYogrt attempts to find libyogrt automatically using standard search paths and compiler information.
If this fails, you can try setting the following environment variables:

* `YOGRT_INCLUDE_PATH`: Path to the directory containing `yogrt.h`.
* `YOGRT_LIBRARY_PATH`: Path to the directory containing `libyogrt.so`.

## Usage

```py
import yogrt

# Get remaining time in seconds:
remaining = yogrt.get_remaining()
```

See `help(yogrt)` or the libyogrt documentation for other methods, but `get_remaining()` is all you need most of the time.
