from __future__ import print_function
# Copyright 2012 the V8 project authors. All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#     * Neither the name of Google Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from os.path import exists
from os.path import isdir
from os.path import join
import os
import platform
import re
import subprocess
import urllib2


### Exit codes and their meaning.
# Normal execution.
EXIT_CODE_PASS = 0
# Execution with test failures.
EXIT_CODE_FAILURES = 1
# Execution with no tests executed.
EXIT_CODE_NO_TESTS = 2
# Execution aborted with SIGINT (Ctrl-C).
EXIT_CODE_INTERRUPTED = 3
# Execution aborted with SIGTERM.
EXIT_CODE_TERMINATED = 4
# Internal error.
EXIT_CODE_INTERNAL_ERROR = 5


def GetSuitePaths(test_root):
  return [ f for f in os.listdir(test_root) if isdir(join(test_root, f)) ]


# Reads a file into an array of strings
def ReadLinesFrom(name):
  lines = []
  with open(name) as f:
    for line in f:
      if line.startswith('#'): continue
      if '#' in line:
        line = line[:line.find('#')]
      line = line.strip()
      if not line: continue
      lines.append(line)
  return lines


def GuessOS():
  system = platform.system()
  if system == 'Linux':
    return 'linux'
  elif system == 'Darwin':
    return 'macos'
  elif system.find('CYGWIN') >= 0:
    return 'cygwin'
  elif system == 'Windows' or system == 'Microsoft':
    # On Windows Vista platform.system() can return 'Microsoft' with some
    # versions of Python, see http://bugs.python.org/issue1082
    return 'windows'
  elif system == 'FreeBSD':
    return 'freebsd'
  elif system == 'OpenBSD':
    return 'openbsd'
  elif system == 'SunOS':
    return 'solaris'
  elif system == 'NetBSD':
    return 'netbsd'
  elif system == 'AIX':
    return 'aix'
  else:
    return None


def UseSimulator(arch):
  machine = platform.machine()
  return (machine and
      (arch == "mipsel" or arch == "arm" or arch == "arm64") and
      not arch.startswith(machine))


# This will default to building the 32 bit VM even on machines that are
# capable of running the 64 bit VM.
def DefaultArch():
  machine = platform.machine()
  machine = machine.lower()  # Windows 7 capitalizes 'AMD64'.
  if machine.startswith('arm'):
    return 'arm'
  elif (not machine) or (not re.match('(x|i[3-6])86$', machine) is None):
    return 'ia32'
  elif machine == 'i86pc':
    return 'ia32'
  elif machine == 'x86_64':
    return 'ia32'
  elif machine == 'amd64':
    return 'ia32'
  elif machine == 's390x':
    return 's390'
  elif machine == 'ppc64':
    return 'ppc'
  else:
    return None


def GuessWordsize():
  if '64' in platform.machine():
    return '64'
  else:
    return '32'


def IsWindows():
  return GuessOS() == 'windows'


def URLRetrieve(source, destination):
  """urllib is broken for SSL connections via a proxy therefore we
  can't use urllib.urlretrieve()."""
  if IsWindows():
    try:
      # In python 2.7.6 on windows, urlopen has a problem with redirects.
      # Try using curl instead. Note, this is fixed in 2.7.8.
      subprocess.check_call(["curl", source, '-k', '-L', '-o', destination])
      return
    except:
      # If there's no curl, fall back to urlopen.
      print("Curl is currently not installed. Falling back to python.")
      pass
  with open(destination, 'w') as f:
    f.write(urllib2.urlopen(source).read())


class FrozenDict(dict):
  def __setitem__(self, *args, **kwargs):
    raise Exception('Tried to mutate a frozen dict')

  def update(self, *args, **kwargs):
    raise Exception('Tried to mutate a frozen dict')


def Freeze(obj):
  if isinstance(obj, dict):
    return FrozenDict((k, Freeze(v)) for k, v in obj.iteritems())
  elif isinstance(obj, set):
    return frozenset(obj)
  elif isinstance(obj, list):
    return tuple(Freeze(item) for item in obj)
  else:
    # Make sure object is hashable.
    hash(obj)
    return obj
