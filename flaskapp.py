import os
import sys
import re
import time
import threading
from flask import Flask

excluded = ["test"]
cwd = os.getcwd()
# print(cwd)
# foldermatch = re.findall("^.+\\\\(.+)$", cwd)
# print(foldermatch[0])
# runfolder = foldermatch[0]
lst_regex = "^AERESGB.*\.lst"

def SearchSubfolder(Subfolder):
    # Input Subfolder is a string, identifying the subfolder to be searched.
    # This should search a given subfolder and return a string:
    # Folder name, present CM loop, and the latest date modified.
    # Example: "a0, 5 CM loops, last modified 2016/05/05 17:32".
    dir_in_folder = os.listdir(cwd + "\\" + Subfolder)
    # Find number of CM loops.
    CMloops = 0
    for element1 in dir_in_folder:
        if (re.match("^CMout0\+_test\\d{1,2}.xlsx$",element1)):
            CMloops += 1
    max_datemod = 0
    for element1 in dir_in_folder:
        datemod = os.path.getmtime(cwd + "\\" + Subfolder + "\\" + element1)
        # os.path.getmtime returns a float representing the datetime.
        if (max_datemod < datemod):
            max_datemod = datemod
    str_latestmod = time.strftime("%Y/%m/%d %I:%M:%S %p", time.localtime(max_datemod))
    out_string = Subfolder + ", " + str(CMloops) + " CM loops, last modified " + str_latestmod
    return(out_string)

def SearchDir():
    # This should search the directory for subfolders.
    # First, get all items in directory.
    subdirs = os.listdir(cwd)
    # Second, get only the subfolders.
    list_dirs = list()
    for element in subdirs:
        if (os.path.isdir(element)):
            list_dirs.append(element)
    # Third, remove those subfolders which are in excluded.
    list_dirs1 = [x for x in list_dirs if x not in excluded]
    # Fourth, check inside each subfolder for AERESGB....lst file using regex.
    non_scenario_folders = list()
    for element in list_dirs1:
        # Searching each subfolder for AERESGB lst file to verify it is a scenario folder.
        dir_in_folder = os.listdir(cwd + "\\" + element)
        has_lst = 0
        for element1 in dir_in_folder:
            if (re.match("^AERESGB.*lst$", element1)):
                has_lst += 1
        if (has_lst == 0):
            non_scenario_folders.append(element)
    list_dirs1 = [x for x in list_dirs1 if x not in non_scenario_folders]
    return(list_dirs1)

def ConstructMultistring(ListSubfolders):
    # Takes as input a list of subfolder names.
    # These names are already cleaned by SearchDir:
    # They contain only bona fide scenario folders.
    # Lists are MUTABLE types, treat this as "pass-by-reference".
    string = "<p>This is a listing of all scenario folders for run: " + cwd + ".</p>\n"
    string += "<p>Scenario Folder Name, Present CM Loop, Latest Date Modified</p>\n"
    for element in ListSubfolders:
        # Now append to string each row corresponding to data.
        string += SearchSubfolder(element) + "<br>\n"
    return(string)

app = Flask(__name__)
@app.route("/")

def main():
    threading.Timer(60.0,main).start()
    listscenfolders = SearchDir()
    multistring = ConstructMultistring(listscenfolders)
    return(multistring)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
