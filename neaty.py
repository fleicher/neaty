from __future__ import print_function

import argparse
import json
import math
import subprocess
from collections import Counter
from typing import List, Dict, Union, Any

from windows import Window, focus_desktop, get_sorted_windows_for_desktop, get_focused_window, get_number_of_monitors, \
    get_focused_desktop, get_desktops_for_monitor, get_position_for_processes, destroy_desktop, create_new_desktop, \
    focus_window_id, move_window, get_app_path


# ################################### #
#  safer move functions (with sleep)  #
# ################################### #


def safe_send_window(desktop: int, window: Window = None):
    import time
    print("Sending {} ({}) to desktop {}".format(window.process, window.id, desktop))
    retries = 0
    window_ids_on_target_desktop: List[Window] = []

    def sent_correctly():
        return window.id in [w.id for w in window_ids_on_target_desktop]

    while retries < 5 and not sent_correctly():
        safe_focus_window_id(window)
        move_window(desktop)
        time.sleep(0.2)
        focus_desktop(desktop)
        time.sleep(0.2)
        window_ids_on_target_desktop = get_sorted_windows_for_desktop(desktop)
        time.sleep(0.2)
        if sent_correctly():
            return
        retries += 1
        print("retry #{}, wanted to sent window {} to {} but that's what's there: {}".format(
            retries, window.id, desktop, window_ids_on_target_desktop))
    else:
        print("Not Successful sending the window to {}.".format(desktop))


def safe_focus_window_id(window: Window):
    import time
    currently_focused_window_id = None
    retries = 0
    while retries < 5 and currently_focused_window_id != window.id:
        focus_window_id(window.id)
        time.sleep(0.2)
        currently_focused_window_id = get_focused_window()
        retries += 1
    assert currently_focused_window_id == window.id, "Problem, the currently focused window is {}".format(
        currently_focused_window_id)


# #################################################################### #
#      standard routine to get ordered numbers for all windows         #
# #################################################################### #

number_of_monitors = get_number_of_monitors()
focused_desktop = get_focused_desktop()
focused_window = get_focused_window()

monitors = {}  # 1-based (note that iterated the other way round)
processes_set = set()
number_of_windows = 1
for monitor_ in range(number_of_monitors, 0, -1):
    desktops_ = {}
    for desktop_ in get_desktops_for_monitor(monitor_):
        windows_ = []
        for window_info_ in get_sorted_windows_for_desktop(desktop_):
            processes_set.add(window_info_.process)
            window_info_.no = number_of_windows
            windows_.append(window_info_)
            number_of_windows += 1
        desktops_[desktop_] = windows_
    monitors[monitor_] = desktops_


# ############################## #
#         Helper functions       #
# ############################## #


def flat_window_list() -> List[Window]:
    return [window for monitor in monitors.values() for desktop in monitor.values() for window in desktop]


def load_preferences() -> Dict[str, Dict[str, Any]]:
    with open("./windows/preferences.json") as f:
        return json.load(f)


def associate_positions_to_windows():
    position_info = get_position_for_processes(list(processes_set))
    for window in flat_window_list():
        for w in position_info[window.process]:
            if w[0] == window.title:
                window.size = w[1]


# associate_positions_to_windows()
# TODO: left window should be shown before right window


def get_icon(process_name: str) -> str:
    import plistlib
    from hashlib import md5
    import os.path

    path = f'./windows/icons/{md5(process_name.encode("utf-8")).hexdigest()}.png'

    if os.path.exists(path):
        return path
    app_path = get_app_path(process_name)
    try:
        process_path = f"{app_path}/Contents"
        with open(process_path + "/Info.plist", "rb") as f:
            icon_name = plistlib.load(f)["CFBundleIconFile"]
            if icon_name[-5:] != ".icns":
                icon_name += ".icns"
        cmd = [
            'sips', '-s', 'format', 'png', f"{process_path}/Resources/{icon_name}",
            '--out', path, '--resampleHeight', '50'
        ]
        result = subprocess.check_output(cmd)
        print(f"created icon for {process_name}:", result)
        return path
    except IOError:
        return 'icons/unknown.png'


def count_unique_processes(monitor: int) -> Counter:
    processes_counter = Counter()
    try:
        for desktop_no, windows in monitors[monitor].items():
            windows_counter = 0
            for window in windows:
                processes_counter[window.process] += 1
                windows_counter += 1
    except KeyError:
        pass
    return processes_counter


# ############################################# #
#         entry points from command line        #
# ############################################# #

def focus_window_number(window_no: int):
    """ entry point for argument --focus"""
    for window in flat_window_list():
        if window.no == window_no:
            print("Focusing to window: ", window.title)
            return safe_focus_window_id(window)


def ordered_windows_for_monitor(monitor_no: int, limit=10) -> str:
    """ entry point for argument --monitor"""
    if monitor_no not in monitors:
        return "[]"
    icon_paths = {process: get_icon(process) for process in processes_set}
    processes_counter = count_unique_processes(monitor_no)
    preferences = load_preferences()
    windows_json: List[Dict[str, Union[str, int]]] = []

    for desktop_no, windows in monitors[monitor_no].items():
        for n, window in enumerate(windows):
            if window.no > limit:
                continue
            short_process_name = preferences["short_names"][window.process] if window.process in preferences[
                "short_names"] else window.process
            short_title = window.title if len(window.title) <= 20 else window.title[:20] + "…"
            windows_json.append({
                "process": short_process_name,
                "short": short_process_name if processes_counter[window.process] == 1 else short_title,
                "short_title": short_title,
                "title": window.title,
                "no": window.no,
                "id": window.id,
                "focused_desktop": focused_desktop == desktop_no,
                "icon": icon_paths[window.process],
                "first": n == 0,  # there is a different css style for the first window of a desktop
                "last": n == len(windows) - 1,
            })
    return json.dumps(windows_json)


def organize(mode="triple"):
    """ entry point for argument --organize"""
    arrangement = load_preferences()["arrangements"][mode]
    left_over_windows = 0
    needed_desktops_counter = Counter()
    existing_desktop_counter = Counter()
    for monitor, desktops in monitors.items():
        for desktop, windows in desktops.items():
            existing_desktop_counter[monitor] += 1
            for window in windows:
                try:
                    target_monitor = arrangement["processes"][window.process]
                    needed_desktops_counter[target_monitor] += 1 / arrangement["monitors"][target_monitor]
                except KeyError:
                    left_over_windows += 1
    for monitor in needed_desktops_counter.keys():
        needed_desktops_counter[monitor] = max(1,  # can't have 0 desktops for a monitor
                                               math.ceil(needed_desktops_counter[monitor]))

    # create or destroy desktops as needed
    for monitor in range(1, number_of_monitors + 1):
        existing = existing_desktop_counter[monitor]
        needed = needed_desktops_counter[monitor]

        for _ in range(abs(existing - needed)):
            if existing > needed:
                destroy_desktop(monitor=monitor)
            else:
                create_new_desktop(monitor=monitor)

    # move windows to target desktops
    windows_counter: Dict[int, int] = Counter({monitor: 0 for monitor in arrangement["monitors"]})
    previous_desktops: Dict[int, int] = {
        int(monitor): sum([needed_desktops_counter[i] for i in range(1, int(monitor))])
        for monitor in arrangement["monitors"]}
    for window in flat_window_list():
        if window.process not in arrangement["processes"]:
            continue
        monitor_to_move_to: int = arrangement["processes"][window.process]
        desktop_to_send_to: int = math.floor(1 + previous_desktops[monitor_to_move_to]
                                             + windows_counter[monitor_to_move_to])
        safe_send_window(desktop=desktop_to_send_to, window=window)
        windows_counter[monitor_to_move_to] += 1 / arrangement["monitors"][str(monitor_to_move_to)]
    print("Finished Moving Windows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--monitor", default=None, help="show windows for this monitor", type=int)
    parser.add_argument("--focus", default=None, help="focus on window #", type=int)
    parser.add_argument("--organize", action="store_true", help="position windows according to standard layout")
    args = parser.parse_args()

    if args.focus is not None:
        focus_window_number(int(args.focus))
    if args.monitor is not None:
        print(ordered_windows_for_monitor(int(args.monitor)))
    if args.organize:
        if number_of_monitors == 3:
            organize("triple")
        else:
            organize("single")
