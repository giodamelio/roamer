"""
This module handles the temp file creation, processing it's output and hand off to the editor
"""

import sys
import tempfile
import os
from subprocess import call

ROAMER_EDITOR = os.environ.get('ROAMER_EDITOR')

if ROAMER_EDITOR:
    EDITOR = ROAMER_EDITOR
else:
    EDITOR = os.environ.get('EDITOR')
    if not EDITOR:
        EDITOR = 'vi'

if ' ' in EDITOR:
    EXTRA_EDITOR_COMMAND = None
else:
    if os.path.basename(EDITOR) in ['vim', 'nvim', 'vi']:
        EXTRA_EDITOR_COMMAND = '+set backupcopy=yes'
    elif os.path.basename(EDITOR) == 'atom':
        EXTRA_EDITOR_COMMAND = '--wait'
    elif os.path.basename(EDITOR) == 'subl':
        EXTRA_EDITOR_COMMAND = '-n -w'
    elif os.path.basename(EDITOR) == 'mate':
        EXTRA_EDITOR_COMMAND = '-w'
    else:
        # nano and emacs work without any extra commands
        EXTRA_EDITOR_COMMAND = None


def file_editor(content):
    with tempfile.NamedTemporaryFile(suffix=".roamer") as temp:
        if sys.version_info[0] == 3:
            content = content.encode('utf-8')
        temp.write(content)
        temp.flush()
        if EXTRA_EDITOR_COMMAND:
            call([EDITOR, EXTRA_EDITOR_COMMAND, temp.name])
        else:
            call(EDITOR.split() + [temp.name])
        temp.seek(0)
        output = temp.read()
        if sys.version_info[0] == 3:
            output = output.decode('UTF-8')
        return output
