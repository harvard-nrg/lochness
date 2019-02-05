import os
import sys
import signal
import atexit

def daemonize(pidfile, stdin='/dev/null', stdout='/dev/null', 
              stderr='/dev/null', wdir='/', sigterm=True):
    '''
    Use double-fork trick to daemonize a program. The second fork only ensures 
	that the daemon cannot reacquire a controlling terminal.

    .. How it works::
        1. parent
           `-- child (fork)

        2. xxx (exit)
           `-- child
               `-- grandchild (fork)

        3.
               xxx (exit)
               `-- grandchild
	
    :param pidfile: Process ID file
    :type pidfile: str
    :param stdin: File to use for standard input
    :type stdin: str
    :param stdout: File to use for standard output
    :type stdout: str
    :param stderr: File to use for standard error
    :type stderr: str
    :param wdir: Working directory
    :type wdir: str
    :param sigterm: Register a dummy SIGTERM handler
    :type sigterm: bool
    '''
    # expand tildes
    pidfile = os.path.expanduser(pidfile)
    stdin = os.path.expanduser(stdin)
    stdout = os.path.expanduser(stdout)
    stderr = os.path.expanduser(stderr)
    # there is only a unified API for getting and setting a umask
    umask = os.umask(0)
    # fork Child
    try:
        pid = os.fork()
    except OSError as e:
        raise DaemonError('first fork failed: %s' % e)
    if pid > 0:
        sys.exit(0) # kill Parent
    # decouple from Parent enviornment
    os.chdir(wdir)
    os.setsid()
    os.umask(umask)
    # fork Grandchild
    try:
        pid = os.fork()
    except OSError as e:
        raise DaemonError('second fork failed: %s' % e)
    if pid > 0:
        sys.exit(0) # kill Child

    # redirect stdin, stdout, and stderr
    sys.stdout.flush()
    sys.stderr.flush()
    stdin = open(stdin, 'r')
    stdout = open(stdout, 'a+')
    stderr = open(stderr, 'a+')
    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())

    # write pid file
    if sigterm:
        signal.signal(signal.SIGTERM, lambda x,y: sys.exit(1))
    atexit.register(lambda: os.remove(pidfile))
    pid = str(os.getpid())
    open(pidfile, 'w+').write('%s' % pid)

class DaemonError(Exception):
    pass
