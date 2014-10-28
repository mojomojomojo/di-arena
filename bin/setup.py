#!/usr/bin/env python3

import sys,os,os.path,shutil,traceback
import subprocess
import re
import zipfile

def detectJava():
    try:
        output = subprocess.check_output(['java','-version'],
                                         stderr = subprocess.STDOUT)
        m = re.search(r'java version "([^"]+)"',output.decode('utf-8'),re.I)
        if m is None:
            print('Cannot discern Java version from output\n\'{0}\''.format(
                output), file=sys.stderr)
            return False

        ver = m.group(1)
        print('Java version {0}'.format(ver))

        javaPath = shutil.which('java')
        if javaPath is None:
            # This really shouldn't happen.
            print('Cannot discern path to Java executable.', file=sys.stderr)
            return False
        print('Java: {0}'.format(javaPath))

        class JavaInfo:
            def __init__(self,path,version):
                self.path,self.version = path,version
        return JavaInfo(javaPath,ver)
    except FileNotFoundError:
        print('Java interpreter is not in the PATH.', file=sys.stderr)
        return False
    except Exception as e:
        print('Java detection failed: {0}'.format(e), file=sys.stderr)
        raise e

def installRobocode( javaPath ):
    installDir = os.path.join(os.path.dirname(__file__),'..','robocode')

    installerDir = os.path.join(os.path.dirname(__file__),'..','install')
    installer_re = re.compile(r'^robocode.*-setup.jar$',re.I)
    for installer in sorted(filter(installer_re.search,
                                   os.listdir(installerDir)),reverse=True):
        print("Installing '{0}' to '{1}'".format(os.path.basename(installer),
                                                 installDir))
        try:
            archive = zipfile.ZipFile(os.path.join(installerDir,installer))
            archive.extractall(path=installDir)

            return installDir
        except Exception as e:
            print('Error installing/extracting Robocode:\n', file=sys.stderr)
            traceback.print_exc()
            return False


if __name__ == '__main__':
    # create any necessary directories
    # detect java
    # install robocode

    javaInfo = detectJava()
    if javaInfo is None:
        sys.exit(1)
    
    roboDir = installRobocode(javaInfo.path)
    if not roboDir:
        sys.exit(1)
