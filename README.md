# RixsToolBox

RixsToolBox is a data analysis software for data collected at the ESRF ID32 RIXS end station. This software is provided "as is". Feature requests and bug reports are very welcome.

## Installation

Make sure you have Python version 3.12 or higher installed on your computer. Then run

```sh
python -m pip install git+https://gitlab.esrf.fr/scientific-software/rixstoolbox.git
```

or

```sh
python -m pip install https://gitlab.esrf.fr/scientific-software/rixstoolbox/-/archive/main/rixstoolbox-main.zip
```

Alternatively download the code, go to the folder and run

```sh
python -m pip install rixstoolbox-main.zip
```

We recommend installation in a dedicated Python virtual environment. The `--ignore-installed` argument may be required if you want to upgrade an existing installation.


## Running the graphical interface

Once installed, you can start the Toolbox by running

```sh
python -m RixsToolBox.RixsToolBox
```


## Citation
If you use this software for your research, you can cite the following paper: [Kurt Kummer et al., J. Synchrotron Rad. <b>24</b>, 531 (2017)](https://doi.org/10.1107/S1600577517000832)
