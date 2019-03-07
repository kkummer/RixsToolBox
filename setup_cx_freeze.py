#!/usr/bin/env python
# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2016-2018 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/

# The application should be built from a virtual environment containing
# only the required packages.

from __future__ import absolute_import, division, unicode_literals

import datetime
now = datetime.datetime.now()

__authors__ = ['Kurt Kummer']
__license__ = 'MIT'
__date__ = '%d-%d-%d' % (now.year, now.month, now.day)

import sys
import os
import zipfile
import glob
import shutil
import uuid
import random

from cx_Freeze import setup, Executable

import numpy
import PyMca5
import fisx


def main():
    from RixsToolBox import RixsToolBoxVersion
    RTB_version = RixsToolBoxVersion()
    install_dir = "./RixsToolBox v%s" % (RTB_version)
    
    print('\n\n')
    print('***********************************************************')
    print('*                                                         *')
    print('*        Freezing RixsToolBox v%s                       *' % RTB_version)
    print('*                                                         *')
    print('***********************************************************')
    print('\n\n')
    
    root = os.path.dirname('.')
    build_dir = os.path.join(root, 'build')
    install_dir = os.path.join(root, install_dir)
    shutil.rmtree(build_dir, ignore_errors=True)
    shutil.rmtree(install_dir, ignore_errors=True)

    # ~ packages = ['matplotlib', 'PyQt5.QtPrintSupport', 'PyMca5.PyMcaGui', 'PyMca5.PyMcaCore']
    packages = ['appdirs', 'packaging']
    includes = ['appdirs', 'packaging.version']
    excludes = ['tkinter', 'scipy']
    excludes = ["Tkinter", "tkinter",
            'tcl','_tkagg', 'Tkconstants',
            "scipy", "Numeric", "numarray"]

    modules = [numpy, PyMca5]
    modules_path = [os.path.dirname(module.__file__) for module in modules]
    include_files = [
        (module, os.path.basename(module)) for module in modules_path]
    
    PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
    include_files.append((os.path.join('C:/windows/system32/', 'VCRUNTIME140.dll')))
    
    fisx_dat_files = os.listdir(os.path.join(
        PYTHON_INSTALL_DIR, 'Lib', 'site-packages', 'fisx', 'fisx_data'))
    fisx_dat_files = [os.path.join(
        PYTHON_INSTALL_DIR, 'Lib', 'site-packages', 'fisx', 'fisx_data', fname)
        for fname in fisx_dat_files if fname.endswith('.dat')]
    include_files += fisx_dat_files
    
    
    options = {
        'build_exe': {
            'packages': packages,
            'includes': includes,
            'excludes': excludes,
            'include_files': include_files,
            'include_msvcr': True,
            'build_exe': build_dir,
            },
        'install_exe': {
            'install_dir': install_dir
            },
        }

    base = None
    if sys.platform == 'win32':
        base = 'Win32GUI'
    base = None
    
    executables = [
        Executable(
            'RixsToolBox.py',
            base=base,
            icon=os.path.join('icons', 'logo.ico'),
            ),
        ]

    setup(
        name='RixsToolBox',
        version=RTB_version,
        options=options,
        executables=executables,
        )
    
    
    # Convinience functions, copying build version into zipfiles
    
    install_dir = "./RixsToolBox v%s" % (RTB_version)
    
    if not sys.platform.startswith('win'):
        install_dir = install_dir.replace(" ","")
    
    
    if os.path.exists(install_dir):
        try:
            def dir_cleaner(directory):
                for f in glob.glob(os.path.join(directory,'*')):
                    if os.path.isfile(f):
                        try:
                            os.remove(f)
                        except:
                            print("file <%s> not deleted" % f)
                    if os.path.isdir(f):
                        dir_cleaner(f)
                try:
                    os.rmdir(directory)
                except:
                    print("directory ", directory, "not deleted")
            dir_cleaner(install_dir)
        except:
            print("Unexpected error:", sys.exc_info())
            pass
    
    # Automatically create the Inno Setup Script file
    rd = random.Random()
    rd.seed(RTB_version)
    iss_file = '\n'.join([
        '[Setup]',
        'AppId={{%s}' % uuid.UUID(int=rd.getrandbits(128)),
        'AppName=RixsToolBox'
        'AppVersion=%s' % RTB_version,
        'AppVerName=RixsToolBox v%s' % RTB_version,
        'AppPublisher=Kurt Kummer',
        'AppPublisherURL=https://github.com/kkummer/RixsToolBox',
        'AppSupportURL=https://github.com/kkummer/RixsToolBox',
        'AppUpdatesURL=https://github.com/kkummer/RixsToolBox/releases',
        'DefaultDirName={pf}\RixsToolBox v%s' % RTB_version,
        'DefaultGroupName=RixsToolBox v%s' % RTB_version,
        ';LicenseFile=..\LICENSE.txt',
        'OutputDir=.\installer',
        'OutputBaseFilename=RixsToolBox-%s-x64' % RTB_version,
        'Compression=lzma',
        'SolidCompression=yes',
        '; Remove for 32-bit applications',
        'ArchitecturesAllowed=x64',
        'ArchitecturesInstallIn64BitMode=x64',
        '',
        '[Languages]',
        'Name: "english"; MessagesFile: "compiler:Default.isl"',
        '',
        '[Files]',
        'Source: ".\RixsToolBox v%s\*"; ' % RTB_version \
        + 'DestDir: "{app}"; Flags: ignoreversion recursesubdirs',
        'Source: "icons\logo.ico"; DestDir: "{app}"',
        '',
        '[Icons]',
        '; Do not forget to copy logo.ico to the build folder.',
        'Name: "{group}\RixsToolBox"; Filename: "{app}\RixsToolBox.exe"; '\
        + 'IconFilename: "{app}\logo.ico"',
        'Name: "{group}\\Uninstall"; Filename: "{uninstallexe}"'
        ])
    with open('create_installer.iss', 'w') as f:
        f.write(''.join(iss_file))
    
    
    print('\n**********************************')
    print('Copying source files into \"%s Source\"' % install_dir)
    
    os.system('mkdir "%s Source"' % install_dir)
    if not sys.platform.startswith('win'):
        os.system('cp ./*.py "%s Source/."' % install_dir)
        os.system('cp ./*.iss "%s Source/."' % install_dir)
    else:
        os.system('copy "./*.py" "%s Source/."' % install_dir)
        os.system('copy "./*.iss" "%s Source/."' % install_dir)
    
    
    print('\n**********************************')
    print('Packing: \"%s Source\" -> \"%s Source.zip\"' % (install_dir, install_dir))
    zipSource = zipfile.ZipFile('%s Source.zip' % (install_dir), 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('%s Source/.' % install_dir):
        for file in files:
            zipSource.write(os.path.join(root, file))
    zipSource.close()
    
    if not sys.platform.startswith('win'):
        os.system('mv "%s" "%s"' % (build_dir, install_dir))
    else:
        os.system('rename "%s" "%s"' % (build_dir, install_dir))
    print('Packing: \"%s\"        -> \"%s.zip\"' % (install_dir, install_dir))
    zipBuild = zipfile.ZipFile('%s.zip' % install_dir, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('%s/.' % install_dir):
        for file in files:
            zipBuild.write(os.path.join(root, file))
    zipBuild.close()
    
    
    sys.exit(0)


if __name__ == '__main__':
    main()
