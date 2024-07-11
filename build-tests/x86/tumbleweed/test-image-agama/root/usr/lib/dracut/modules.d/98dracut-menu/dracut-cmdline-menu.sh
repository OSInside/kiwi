#!/bin/sh

if [ -d /sysroot  ] ; then
  type getarg > /dev/null 2>&1 || . /lib/dracut-lib.sh
  getarg "rd.cmdline=menu" || exit 0
fi

# -----------------------------------------------------------------------------


# usage example:
#
# title="Foo menu"
# items=("Foo A" "Foo B" "Foo C")
#
# dia_menu title items selected_item
#
# echo "selected_item=$selected_item"
#
dia_menu () {
  local -n x_title=$1
  local -n x_list=$2
  local -n x_item=$3

  local tmp i ind ok

  until [[ "$ok" ]] ; do
    echo -e "\n$x_title\n"

    echo "0) <-- Back <--"
    ind=1
    for i in "${x_list[@]}" ; do
      echo "$ind) $i"
      ind=$((ind + 1))
    done

    echo

    read -e -r -p "> " x_item tmp

    [[ ( -z "$x_item" || "$x_item" = $((x_item)) ) && "$x_item" -lt $ind ]] && ok=1
  done

  x_item=$((x_item))

  return 0
}


# usage example
#
# title="Foo input"
# value="foo bar"
# dia_input title value
# aborted=$?
# 
# if [ $aborted = 1 ] ; then
#   echo aborted
# else
#   echo -e "input=\"$value\""
# fi
#
dia_input () {
  local -n x_title=$1
  local -n x_value=$2

  local tmp="$x_value"

  echo -e "\n${x_title}. (Enter '+++' to abort.)\n"

  read -e -r -p "[$tmp]> " -i "$tmp" tmp

  if [[ "$tmp" = "${tmp%+++}+++" ]] ; then
    return 1
  else
    x_value="$tmp"
  fi

  return 0
}

# -----------------------------------------------------------------------------

echo
echo "== Additional parameters =="

live_root=$(getarg "root=")
live_root_disk=$(getarg "root_disk=")
live_root_net=$(getarg "root_net=")
live_proxy=$(getarg "proxy=")

live_root_disk=${live_root_disk:-$live_root}

live_root=${live_root#live:}
live_root_disk=${live_root_disk#live:}
live_root_net=${live_root_net#live:}

aborted=1

while [ "$aborted" != 0 ] ; do
  echo -n > /etc/cmdline.d/98-cmdline-menu.conf

  title="Live image location"
  items=("Disk / DVD" "Network")
  dia_menu title items selected_item

  aborted=$?
  [[ $aborted != 0 ]] && continue

  case $selected_item in
    1) live_root="$live_root_disk" ;;
    2) live_root="$live_root_net" ;;
  esac

  if [[ "$selected_item" = 2 ]] ; then
    title="Live image location (e.g. http://example.com/live.iso)"
    dia_input title live_root
    aborted=$?
    [[ $aborted != 0 ]] && continue

    live_root_net="$live_root"

    title="Proxy Settings (e.g. http://proxy.example.com)"
    dia_input title live_proxy

    aborted=$?
    [[ $aborted != 0 ]] && continue
  fi

  echo "root=live:$live_root" >> /etc/cmdline.d/98-cmdline-menu.conf
  echo "proxy=$live_proxy" >> /etc/cmdline.d/98-cmdline-menu.conf

  echo
  echo "== Updated settings =="
  echo
  cat /etc/cmdline.d/98-cmdline-menu.conf

  title="Settings ok?"
  items=("Yes" "No")
  dia_menu title items selected_item

  [[ $selected_item = 1 ]] && break

  aborted=1
done
