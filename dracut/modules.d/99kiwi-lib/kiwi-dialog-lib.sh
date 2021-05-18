type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

function run_dialog {
    # """
    # Run the dialog program via the systemd service either in a
    # framebuffer terminal or on the console. The return code of
    # the function is the return code of the dialog call. The
    # output of the dialog call is stored in a file and can be
    # one time read via the get_dialog_result function
    # """
    stop_plymouth
    local dialog_result=/tmp/dialog_result
    local dialog_exit_code=/tmp/dialog_code
    {
        echo "dialog $* 2>$dialog_result"
        echo "echo -n \$? >$dialog_exit_code"
    } >/bin/dracut-interactive
    _run_interactive
    return "$(cat $dialog_exit_code)"
}

function setup_progress_fifo {
    local fifo=$1
    export current_progress_fifo="${fifo}"
    [ -e "${fifo}" ] || mkfifo "${fifo}"
}

function stop_dialog {
    _stop_interactive
}

function run_progress_dialog {
    # """
    # Run the gauge dialog via systemd reading progress
    # status information from stdin
    # """
    stop_plymouth
    declare fifo=${current_progress_fifo}
    local title=$1
    local backtitle=$2
    local progress_at="${fifo}"
    if [ ! -e "${progress_at}" ];then
        return
    fi
    {
        echo -n "cat ${fifo} | dialog --backtitle \"${backtitle}\" "
        echo -n "--gauge \"${title}\"" 7 65 0
        echo
    } >/bin/dracut-interactive
    _run_interactive
}

function get_dialog_result {
    local dialog_result=/tmp/dialog_result
    [ -e "${dialog_result}" ] && cat ${dialog_result}; rm -f ${dialog_result}
}

function stop_plymouth {
    if command -v plymouth &>/dev/null;then
        plymouth --quit --wait
    fi
}

#=========================================
# Methods considered private
#-----------------------------------------
function _setup_interactive_service {
    local service=/usr/lib/systemd/system/dracut-run-interactive.service
    local script=/bin/dracut-interactive
    [ -e ${service} ] && return
    {
        echo "[Unit]"
        echo "Description=Dracut Run Interactive"
        echo "DefaultDependencies=no"
        echo "After=systemd-vconsole-setup.service"
        echo "Wants=systemd-vconsole-setup.service"
        echo "Conflicts=emergency.service emergency.target"
        echo "[Service]"
        echo "Environment=HOME=/"
        echo "Environment=DRACUT_SYSTEMD=1"
        echo "Environment=NEWROOT=/sysroot"
        echo "WorkingDirectory=/"
        if _fbiterm_ok; then
            echo "ExecStart=fbiterm -- /bin/bash ${script} "
        else
            echo "ExecStart=/bin/bash ${script}"
        fi
        echo "Type=oneshot"
        echo "StandardInput=tty-force"
        echo "StandardOutput=inherit"
        echo "StandardError=inherit"
        echo "KillMode=process"
        echo "IgnoreSIGPIPE=no"
        echo "KillSignal=SIGHUP"
    } > ${service}
}

function _run_interactive {
    _setup_interactive_service
    systemctl start dracut-run-interactive.service
}

function _stop_interactive {
    systemctl stop dracut-run-interactive.service
}

function _fbiterm_ok {
    if [ ! -e /dev/fb0 ];then
        # no framebuffer device found
        return 1
    fi
    if ! command -v fbiterm &>/dev/null;then
        # no framebuffer terminal program found
        return 1
    fi
    if command -v isconsole &>/dev/null;then
        if ! isconsole;then
            # inappropriate ioctl (not a linux console)
            return 1
        fi
    elif ! fbiterm echo &>/dev/null;then
        # fbiterm can't be called with echo test cmd
        return 1
    fi
    return 0
}
