from __future__ import print_function
import subprocess
from typing import List, Dict, Tuple, Optional


class Window:
    def __init__(self, items: List[str]):
        self.id = int(items[0])
        self.process = items[1]
        self.title: str = items[2]
        self.no: Optional[int] = None
        self.movable: Optional[bool] = None
        self.role: Optional[str] = None
        self.resizable: Optional[bool] = None

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


def get_file_for_processes(processes: List[str]) -> Dict[str, str]:
    import applescript
    script = 'tell application "System Events"\n\treturn { ' + ", ".join([
        f'file of application process "{process}"' for process in processes
    ]) + ' }\nend tell'
    return {process: path for process, path in zip(processes, applescript.AppleScript(script).run())}


def get_app_path(process: str) -> str:
    import applescript
    try:
        script = f'''
        tell application "System Events"
            return file of application process "{process}"
        end tell'''
        app_path = applescript.AppleScript(script).run()
    except applescript.ScriptError:
        print(f"Could not load appfile for {process}, will guess")
        from fuzzywuzzy import fuzz
        import os
        best_ratio = 0
        app_path = None
        for f in os.scandir("/Applications/"):
            ratio = fuzz.ratio(f.name[:-4], process)
            if ratio > best_ratio:
                best_ratio = ratio
                app_path = f.path
        print(f"guessing to be {app_path}")
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

    windows = []
    for line in output.split("\n"):
        if line[0] == " ":
            # windows[-1].title = line.strip()
            continue

        items = [item.strip() for item in line.split(",")]
        if items[-1] == "(invalid)":  # small pseudo windows are noted this way.
            continue

        window = Window(items)
        if only_resizable:
            window.calc_window_details()
            if not window.resizable:
                continue  # these are small fake windows that don't have to be addressed.
        windows.append(window)
    return sorted(windows, key=lambda wind: wind.id)
