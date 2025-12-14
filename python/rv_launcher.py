import nuke
import os
import subprocess
import platform
import re
import glob

def get_rv_path():
    system = platform.system()
    if system == "Windows":
        search_paths = [
            r"C:\Program Files\ShotGrid",
            r"C:\Program Files\Shotgun",
        ]
        for root in search_paths:
            if not os.path.exists(root):
                continue
            for folder in os.listdir(root):
                bin_path = os.path.join(root, folder, "bin", "rv.exe")
                if os.path.exists(bin_path):
                    return bin_path
        return None
    elif system == "Darwin":
        mac_paths = [
            "/Applications/RV.app/Contents/MacOS/RV",
            "/usr/local/bin/rv"
        ]
        for p in mac_paths:
            if os.path.exists(p):
                return p
        return None
    elif system == "Linux":
        linux_paths = [
            "/usr/local/bin/rv",
            "/usr/bin/rv"
        ]
        for p in linux_paths:
            if os.path.exists(p):
                return p
        return None
    return None

def extract_sequence_info(file_path):
    if file_path.lower().endswith(('.mov', '.mp4', '.avi', '.mxf', '.m4v', '.wmv', '.mpg', '.mpeg')):
        if os.path.exists(file_path):
            return file_path, 1, 1
        return None, None, None

    match = re.search(r'%0(\d+)d', file_path)
    if match:
        padding = int(match.group(1))
        frame_pattern = '%0{}d'.format(padding)
    else:
        hash_match = re.search(r'(#+)', file_path)
        if hash_match:
            padding = len(hash_match.group(1))
            file_path = file_path.replace('#' * padding, '%%0%dd' % padding)
            frame_pattern = '%%0%dd' % padding
        else:
            return None, None, None

    glob_pattern = re.sub(r'%0\d+d', '[0-9]' * padding, file_path)
    directory = os.path.dirname(file_path)
    pattern = os.path.join(directory, os.path.basename(glob_pattern))

    files = sorted(glob.glob(pattern))
    if not files:
        return None, None, None

    base = os.path.basename(file_path)
    prefix, suffix = base.split(frame_pattern)
    frame_numbers = []

    for f in files:
        name = os.path.basename(f)
        number = name[len(prefix):-len(suffix)] if suffix else name[len(prefix):]
        if number.isdigit():
            frame_numbers.append(int(number))

    if not frame_numbers:
        return None, None, None

    start = min(frame_numbers)
    end = max(frame_numbers)
    first_file = file_path.replace(frame_pattern, str(start).zfill(padding))
    return first_file, start, end

def launch_rv():
    sel = nuke.selectedNodes()
    if not sel:
        nuke.message("Please select one or more Read or Write nodes.")
        return

    rv_path = get_rv_path()
    if not rv_path:
        nuke.message("Please Install RV on Your System")
        return

    args = [rv_path]

    for node in sel:
        if node.Class() not in ["Read", "Write"]:
            continue

        try:
            raw_path = node['file'].value().replace("\\", "/")
        except:
            continue

        try:
            raw_path = nuke.filename(node).replace("\\", "/")
        except:
            pass

        first_file, start, end = extract_sequence_info(raw_path)
        if not first_file or not os.path.exists(first_file):
            nuke.message(f"Cannot find valid sequence for:\n{raw_path}")
            return

        args.append(first_file)
        args.extend(["-in", str(start), "-out", str(end)])

    if len(args) == 1:
        nuke.message("No valid files to open in RV.")
        return

    try:
        subprocess.Popen(args)
    except Exception as e:
        nuke.message("Failed to launch RV:\n" + str(e))
