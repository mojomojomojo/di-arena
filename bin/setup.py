#!/usr/bin/env python3

import sys,os,os.path,shutil,traceback
import subprocess
import re
import zipfile

def detectJava( exe, version_re ):
    try:
        output = subprocess.check_output([exe,'-version'],
                                         stderr = subprocess.STDOUT)
        m = version_re.search(output.decode('utf-8'))
        if m is None:
            print('Cannot discern {0} version from output\n\'{1}\''.format(
                exe,output), file=sys.stderr)
            return False

        ver = m.group(1)
        print('{0} version {1}'.format(exe,ver))

        javaPath = shutil.which(exe)
        if javaPath is None:
            # This really shouldn't happen.
            print('Cannot discern path to {0} executable.'.format(exe),
                  file=sys.stderr)
            return False
        print('{0}: {1}'.format(exe,javaPath))

        class JavaInfo:
            def __init__(self,path,version):
                self.path,self.version = path,version
        return JavaInfo(javaPath,ver)
    except FileNotFoundError:
        print('{0} is not in the PATH.'.format(exe), file=sys.stderr)
        return False
    except Exception as e:
        print('{0} detection failed: {1}'.format(exe,e), file=sys.stderr)
        raise e

def installRobocode( javaPath ):
    installDir = os.path.join(os.path.dirname(__file__),'..','robocode')
    if os.path.isdir(installDir):
        try:
            shutil.rmtree(installDir)
        except Exception as e:
            print('Error removing existing Robocode install dir: {0}'.format(e),
                  file = sys.stderr)
            traceback.print_exc()
            return False

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

    javaInfo = detectJava('java',re.compile(r'java version "([^"]+)"',re.I))
    if not javaInfo:
        sys.exit(1)
    javacInfo = detectJava('javac',re.compile(r'javac (\S+)',re.I))
    if not javacInfo:
        sys.exit(1)
    
    roboDir = installRobocode(javaInfo.path)
    if not roboDir:
        sys.exit(1)
