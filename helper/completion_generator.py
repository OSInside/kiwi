#!/usr/bin/python3

from textwrap import dedent

import subprocess
import re

import collections


class AutoVivification(dict):
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


class AppHash:
    def __init__(self):  # noqa: C901
        tasks = [
            'kiwi/cli.py',
            'kiwi/tasks/*.py'
        ]
        call_parm = ['bash', '-c', 'cat %s' % ' '.join(tasks)]
        cmd = subprocess.Popen(
            call_parm, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        begin = False
        cur_path = ''
        self.result = AutoVivification()
        for line in cmd.communicate()[0].decode().split('\n'):
            usage = re.search('^usage: (.*)', line)
            if usage:
                begin = True
                if re.match('.*--help', line):
                    mod_line = re.sub('[\[\]\|]', '', usage.group(1))
                    mod_line = re.sub('-h ', '', mod_line)
                    key_list = mod_line.split()
                    result_keys = self.validate(key_list)
                    cur_path = self.merge(result_keys, self.result)
                else:
                    key_list = usage.group(1).split()
                    result_keys = self.validate(key_list)
                    cur_path = self.merge(result_keys, self.result)
            elif begin:
                if not line:
                    begin = False
                else:
                    if re.match('.*--version', line):
                        mod_line = re.sub('[\[\]\|]', '', line)
                        mod_line = re.sub('-v ', '', mod_line)
                        key_list = mod_line.split()
                        result_keys = self.validate(key_list)
                        cur_path = self.merge(result_keys, self.result)
                    elif re.match('.*kiwi-ng --compat', line):
                        mod_line = re.sub('[\[\]\|]', '', line)
                        mod_line = re.sub('<legacy_args>...', '', mod_line)
                        key_list = mod_line.split()
                        result_keys = self.validate(key_list)
                        cur_path = self.merge(result_keys, self.result)
                    elif re.match('.*kiwi-ng \[', line):
                        line = line.replace('[', '')
                        line = line.replace(']', '')
                        line = line.replace('|', '')
                        key_list = line.split()
                        key_list.pop(0)
                        for global_opt in key_list:
                            result_keys = self.validate(
                                ['kiwi-ng', global_opt]
                            )
                            cur_path = self.merge(result_keys, self.result)
                    elif re.match('            \[', line):
                        line = line.replace('[', '')
                        line = line.replace(']', '')
                        line = line.replace('|', '')
                        key_list = line.split()
                        for global_opt in key_list:
                            result_keys = self.validate(
                                ['kiwi-ng', global_opt]
                            )
                            cur_path = self.merge(result_keys, self.result)
                    elif re.match('                \[', line):
                        opt_val = re.search('                \[(--.*)', line)
                        global_opt = opt_val.group(1)
                        global_opt = global_opt.replace('[', '')
                        global_opt = global_opt.replace(']', '')
                        global_opt = global_opt.replace('|', '')
                        result_keys = self.validate(
                            ['kiwi-ng', global_opt]
                        )
                        cur_path = self.merge(result_keys, self.result)
                    elif re.match('.*kiwi', line):
                        mandatory_options = re.search(
                            '(.*kiwi-ng.*?) (--.*)', line
                        )
                        if mandatory_options:
                            line = mandatory_options.group(1)
                        key_list = line.split()
                        result_keys = self.validate(key_list)
                        cur_path = self.merge(result_keys, self.result)
                        if mandatory_options:
                            for option in mandatory_options.group(2).split():
                                mod_line = cur_path + ' ' + option
                                key_list = mod_line.split()
                                result_keys = self.validate(key_list)
                                self.merge(result_keys, self.result)
                    else:
                        if 'kiwi-ng --' in cur_path:
                            cur_path = ''
                        for mod_line in line.strip().split('|'):
                            mod_line = cur_path + ' ' + mod_line
                            mod_line = re.sub('[\[\]]', '', mod_line)
                            mod_line = re.sub('-h ', '', mod_line)
                            key_list = mod_line.split()
                            result_keys = self.validate(key_list)
                            self.merge(result_keys, self.result)

    def merge(self, key_list, result):
        raw_key_path = " ".join(key_list)
        key_path = ''
        for key in key_list:
            key_path += '[\'' + key + '\']'
        expression = 'self.result' + key_path
        exec(expression)
        return raw_key_path

    def validate(self, key_list):
        result_keys = []
        for key in key_list:
            option = re.search('^\[(--.*)=|^\[(.*)\]', key)
            mandatory = re.search('^(--.*)=', key)
            if option:
                if option.group(1):
                    result_keys.append(option.group(1))
            elif mandatory:
                if mandatory.group(1):
                    result_keys.append(mandatory.group(1))
            elif re.search('<servicename>|<command>|<args>...', key):
                pass
            else:
                key = key.replace('<', '__')
                key = key.replace('>', '__')
                result_keys.append(key)
        return result_keys


class AppTree:
    def __init__(self):
        self.completion = AppHash()
        self.level_dict = {}

    def traverse(self, tree=None, level=0, origin=None):
        if not tree:
            tree = self.completion.result['kiwi-ng']
        if not origin:
            origin = 'kiwi-ng'
        for key in tree:
            try:
                if self.level_dict[str(level)]:
                    pass
            except KeyError:
                self.level_dict[str(level)] = {}
            try:
                if self.level_dict[str(level)][origin]:
                    pass
            except KeyError:
                self.level_dict[str(level)][origin] = []

            if key not in self.level_dict[str(level)][origin]:
                self.level_dict[str(level)][origin].append(key)

            if tree[key]:
                self.traverse(tree[key], level + 1, key)


tree = AppTree()
tree.traverse()

# helpful for debugging
# pp = pprint.PrettyPrinter(indent=4)
# pp.pprint(tree.completion.result)

sorted_levels = collections.OrderedDict(
    sorted(tree.level_dict.items())
)

print(dedent('''
#========================================
# _kiwi
#----------------------------------------
function setupCompletionLine {
    local comp_line=$(echo $COMP_LINE | sed -e 's@kiwi-ng@kiwi@')
    local result_comp_line
    local prev_was_option=0
    for item in $comp_line; do
        if [ $prev_was_option = 1 ];then
            prev_was_option=0
            continue
        fi
        if [[ $item =~ -.* ]];then
            prev_was_option=1
            continue
        fi
        result_comp_line="$result_comp_line $item"
    done
    echo $result_comp_line
}

function _kiwi {
    local cur prev opts
    _get_comp_words_by_ref cur prev
    local cmd=$(setupCompletionLine | awk -F ' ' '{ print $NF }')
''').strip())

print('    for comp in $prev $cmd;do')
print('        case "$comp" in')
for level in sorted_levels:
    if level == '0':
        continue
    for sub in sorted(sorted_levels[level]):
        print('            "%s")' % (sub))
        print(
            '                __comp_reply "{0}"'.format(
                (" ".join(sorted(sorted_levels[level][sub])))
            )
        )
        print('                return 0')
        print('                ;;')
print('        esac')
print('    done')
print(
    '    __comp_reply "{0}"'.format(
        (" ".join(sorted(sorted_levels['0']['kiwi-ng'])))
    )
)
print('    return 0')
print('}')
print(dedent('''
#========================================
# comp_reply
#----------------------------------------
function __comp_reply {
    word_list=$@
    COMPREPLY=($(compgen -W "$word_list" -- ${cur}))
}

complete -F _kiwi -o default kiwi
complete -F _kiwi -o default kiwi-ng
''').strip())
