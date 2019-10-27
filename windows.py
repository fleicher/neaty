from __future__ import print_function

import json
import subprocess
import time
from typing import List, Dict, Tuple, Optional, Any


class Window:
    def __init__(self, items: List[str]):
        self.id = int(items[0])
        self.process = items[1]
        self.title: str = items[2]
        self.no: Optional[int] = None
        self.movable: Optional[bool] = None
        self.role: Optional[str] = None
        self.resizable: Optional[bool] = None
        self.position: Optional[Tuple[int, int]] = None

    def calc_window_details(self):
        rows = subprocess.check_output([
            '/usr/local/bin/chunkc', 'tiling::query', '--window', str(self.id)
        ]).decode('utf-8').strip().split("\n")
        output = {row[:row.index(":")]: row[row.index(":") + 1:] for row in rows if row.find(":") >= 0}
        self.movable = bool(int(output["movable"]))
        self.role = output["role"]
        self.resizable = bool(int(output["resizable"]))

    def __repr__(self):
        return f"{self.id} - {self.process} [{self.title[:20]}]"


# ################################ #
#          Focus Methods           #
# ################################ #


def get_number_of_monitors() -> int:
    return int(subprocess.check_output([
        '/usr/local/bin/chunkc', 'tiling::query', '--monitor', 'count'
    ]).decode('utf-8'))


def get_focused_desktop() -> int:
    return int(subprocess.check_output([
        '/usr/local/bin/chunkc', 'tiling::query', '--desktop', 'id'
    ]).decode('utf-8'))


def get_focused_window() -> int:
    return int(subprocess.check_output([
        '/usr/local/bin/chunkc', 'tiling::query', '--window', 'id'
    ]).decode('utf-8'))


def focus_monitor(monitor: int):
    return subprocess.check_output([
        '/usr/local/bin/chunkc', 'tiling::monitor', '-f', str(monitor)
    ])


def focus_desktop(desktop: int):
    return subprocess.check_output([
        '/usr/local/bin/chunkc', 'tiling::desktop', '--focus', str(desktop)
    ])


def focus_window_id(window_id: int):
    return subprocess.check_output([
        '/usr/local/bin/chunkc', 'tiling::window', '--focus', str(window_id)
    ])


# ################################ #
#   Desktop Manipulation Functions #
# ################################ #


def create_new_desktop(monitor: Optional[int] = None):
    if monitor is not None:
        focus_monitor(monitor)
    return subprocess.check_output([
        '/usr/local/bin/chunkc', 'tiling::desktop', '--create'
    ])


def destroy_desktop(monitor: Optional[int] = None):
    if monitor is not None:
        focus_monitor(monitor)
    return subprocess.check_output([
        '/usr/local/bin/chunkc', 'tiling::desktop', '--annihilate'
    ])


def move_desktop(monitor: int, desktop: Optional[int] = None):
    if desktop is not None:
        focus_desktop(desktop)
    return subprocess.check_output([
        '/usr/local/bin/chunkc', 'tiling::desktop', '--move', str(monitor)
    ])


def move_window(desktop: int):
    return subprocess.check_output([
        '/usr/local/bin/chunkc', 'tiling::window', '--send-to-desktop', str(desktop)
    ])


# #################################### #
#       Retrieve Details Functions     #
# #################################### #


def get_desktops_for_monitor(monitor: int) -> List[int]:
    """ desktops and monitors both are 1-based """
    return [
        int(no) for no in subprocess.check_output([
            '/usr/local/bin/chunkc',
            'tiling::query',
            '--desktops-for-monitor',
            str(monitor)
        ]).decode('utf-8').strip().split(" ")
    ]


def get_positions_for_process(process: str) -> Dict[str, List[int]]:
    import json
    result = subprocess.run(["sh", "./windows/window_position.sh", process], stdout=subprocess.PIPE).stdout
    windows = {}
    for line in result.decode('utf-8').split("\n"):
        if line.strip() == "":
            continue
        pos, title = line.split(":@:")
        windows[title.strip()] = json.loads(pos)
    return windows


def get_position_for_processes(processes: List[str]) -> Dict[str, List[Tuple[str, Tuple[float, float]]]]:
    import applescript
    script = 'tell application "System Events"\n\treturn {' + ", ".join([
        '({position, size, title} of every window of application process "' + process + '")'
        for process in processes
    ]) + '}\nend tell'
    output = applescript.AppleScript(script).run()
    result = {}
    for process_name, (positions, sizes, titles) in zip(processes, output):
        result[process_name] = [
            (title, position) for position, size, title in zip(positions, sizes, titles)
        ]
    return result


def get_app_path(process: str) -> str:
    import applescript
    try:
        script = f'''
        tell application "System Events"
            return file of application process "{process}"
        end tell'''
        app_path = applescript.AppleScript(script).run()
    except applescript.ScriptError:
        subprocess.check_output(["sh", "windows/window_position.sh"])  # asking for permission

        # print(f"Could not load appfile for {process}, will guess")
        from fuzzywuzzy import fuzz
        import os
        best_ratio = 0
        app_path = None
        for f in os.scandir("/Applications/"):
            ratio = fuzz.ratio(f.name[:-4], process)
            if ratio > best_ratio:
                best_ratio = ratio
                app_path = f.path
        # print(f"guessing to be {app_path}")
    return app_path


def get_sorted_windows_for_desktop(desktop: int, *, only_resizable=False) -> List[Window]:
    output = subprocess.check_output([
        '/usr/local/bin/chunkc',
        'tiling::query',
        '--windows-for-desktop',
        str(desktop)
    ]).decode('utf-8').strip()
    if output == "":
        return []

    output_by_lines = []
    for line in output.split("\n"):
        try:
            int(line[0])  # to throw Value Error if there is no PID in output
            output_by_lines.append([item.strip() for item in line.split(",")])
        except ValueError:  # this was a line with a line break (i.e. first character not PID)
            output_by_lines[-1][-1] += "\n" + line

    windows = []
    for items in output_by_lines:
        if items[2][-9:] == "(invalid)":
            continue  # pseudo windows (e.g. Chrome's find dialog)

        window = Window(items)
        if only_resizable:
            window.calc_window_details()
            if not window.resizable:
                continue  # these are small fake windows that don't have to be addressed.
        windows.append(window)
    return sorted(windows, key=lambda wind: wind.id)


prev_positions: Optional[Dict[str, Dict[str, Any]]] = None


# format: {
#   "processes": {
#     "Firefox": 324342.2342, "PyCharm": 2334234.23
#   },
#   "windows":   {
#     "-9242342343": [423424243.24234,  [720, 0]]},
#     "20493":       [2342424243.24234, [0, 430]]}
#   }
# }


def get_position(process: str, title: str) -> Optional[Tuple[int, int]]:
    global prev_positions
    title = title.strip()
    if prev_positions is None:
        try:
            with open(".windows/positions.json") as f:
                prev_positions = json.load(f)
        except FileNotFoundError:
            prev_positions = {"processes": {}, "windows": {}}

    current_time = time.time()
    windows = prev_positions["windows"]
    processes = prev_positions["processes"]
    if title in windows and current_time - windows[title][0] < 60:
        return windows[title][1]

    if process not in processes or current_time - processes[process] > 60:
        # NOT return None  # asked to recently, will not go again

        # will actually have to update for this key
        found_windows = get_positions_for_process(process)
        prev_positions["processes"][process] = current_time
        if found_windows:
            # the request did deliver results
            for found_window_title, position in found_windows.items():
                prev_positions["windows"][found_window_title.strip()] = [current_time, position]
                # TODO: need a cleep-up of very old time stamps
            with open("./windows/positions.json", "w+") as f:
                json.dump(prev_positions, f)
            if title in windows:
                return windows[title][1]
    highest_ratio = 0
    highest_info: Optional[Tuple[int, int]] = None
    from fuzzywuzzy import fuzz
    for t, info in prev_positions["windows"].items():
        ratio = fuzz.ratio(t, title)
        if ratio > highest_ratio:
            highest_info = info[1]
            highest_ratio = ratio
    return highest_info if highest_ratio > 0.5 else None


def get_icon_path(process_name: str) -> str:
    import plistlib
    import os.path

    path = f'./windows/icons/{process_name}.png'
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
        subprocess.run(cmd, stdout=subprocess.PIPE)
        return path
    except IOError:
        return 'icons/unknown.png'
