# standard library modules, , ,
import os
import subprocess
import tempfile
import logging

# fsutils, , misc filesystem utils, internal
import fsutils

git_logger = logging.getLogger('git')



class VCS(object):
    @classmethod
    def cloneToTemporaryDir(cls, remote):
        raise NotImplementedError()

    @classmethod
    def cloneToDirectory(cls, remote, directory, tag=None):
        raise NotImplementedError()

    def isClean(self):
        raise NotImplementedError()
    def commit(self, message, tag=None):
        raise NotImplementedError()
    def isClean(self):
        raise NotImplementedError()
    def tags(self):
        raise NotImplementedError()
    def markForCommit(self, path):
        pass
    def remove(self):
        raise NotImplementedError()
    def __nonzero__(self):
        raise NotImplementedError()
    

class Git(VCS):
    def __init__(self, path):
        self.worktree = path
        self.gitdir = os.path.join(path, '.git')

    @classmethod
    def cloneToTemporaryDir(cls, remote):
        return cls.cloneToDirectory(remote, tempfile.mkdtemp())
    
    @classmethod
    def cloneToDirectory(cls, remote, directory, tag=None):
        commands = [
            ['git', 'clone', remote, directory]
        ]
        for cmd in commands:
            git_logger.debug('will clone %s into %s', remote, directory)
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
            git_logger.debug('clone %s into %s: %s', remote, directory, out or err)
            if child.returncode:
                raise Exception('failed to clone repository %s: %s', remote, err or out)
        r = Git(directory)
        if tag is not None:
            r.updateToTag(tag)
        return r


    def remove(self):
        fsutils.rmRf(self.worktree)

    def workingDirectory(self):
        return self.worktree

    def _gitCmd(self, *args):
        return ['git','--work-tree=%s' % self.worktree,'--git-dir=%s'%self.gitdir] + list(args);

    def _execCommands(self, commands):
        out, err = None, None
        for cmd in commands:
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
            if child.returncode:
                raise Exception('command failed: %s:%s', cmd, err or out)
        return out, err

    def isClean(self):
        commands = [
            self._gitCmd('diff', '--quiet', '--exit-code'),
            self._gitCmd('diff', '--cached', '--quiet', '--exit-code'),
        ]
        for cmd in commands:
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
            if child.returncode:
                return False
        return True

    def markForCommit(self, relative_path):
        commands = [
            self._gitCmd('add', os.path.join(self.worktree, relative_path)),
        ]
        self._execCommands(commands)
    
    def updateToTag(self, tag):
        commands = [
            self._gitCmd('checkout', tag),
        ]
        self._execCommands(commands)

    
    def tags(self):
        commands = [
            self._gitCmd('tag', '-l')
        ]
        out, err = self._execCommands(commands)
        return out.split('\n')

    def commit(self, message, tag=None):
        commands = [
            self._gitCmd('commit', '-m', message),
        ]
        if tag:
            commands.append(
                self._gitCmd('tag', tag),
            )
        for cmd in commands:
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
            if child.returncode:
                raise Exception('command failed: %s:%s', cmd, err or out)

    def __nonzero__(self):
        return True


class HG(VCS):
    pass

def getVCS(path):
    # crude heuristic, does the job...
    if os.path.isdir(os.path.join(path, '.git')):
        return Git(path)
    if os.path.isdir(os.path.join(path, '.hg')):
        return HG(path)
    return None


