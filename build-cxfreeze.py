import os
import sys

cwd = os.path.abspath(os.getcwd())
cmd = r'cd %s ; "%s" cx_setup.py build_exe' % (
    os.path.join(".", "package", "cxfreeze"),
    sys.executable,
)

if sys.platform.startswith("win"):
    cmd = cmd.replace(";", "&")
result = os.system(cmd)

os.chdir(cwd)
if result:
    print("Unsuccessful command <%s>" % cmd)
    sys.exit(result)
else:
    import glob
    import shutil

    # Create the dist directory.
    dist = os.path.join(cwd, "dist")
    if not os.path.exists(dist):
        os.mkdir(dist)
    # Move the frozen installer.
    installer = glob.glob(os.path.join(".", "package", "cxfreeze", "Rixs*.exe"))
    if not len(installer):
        print("Could not generate installer")
        sys.exit(1)
    source = installer[0]
    target = os.path.join(dist, os.path.basename(source))
    if os.path.exists(target):
        os.remove(target)
    shutil.move(source, target)
    # Cleanup
    os.remove(os.path.join(".", "package", "cxfreeze", "nsisscript.nsi"))
    shutil.rmtree(os.path.join(".", "package", "cxfreeze", "build"))
