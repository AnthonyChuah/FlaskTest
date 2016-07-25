import os
import sys
import subprocess
import re
import time
import datetime
import threading
from flask import Flask, request, session, g, redirect, url_for, render_template, flash

### SECTION_TRACKER ###

portnum = sys.argv[1]
print("Port number is:")
print(portnum)
excluded = ["dummy"]
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
    dt_latestmod = datetime.datetime.strptime(str_latestmod, "%Y/%m/%d %I:%M:%S %p")
    # If the latest modified is more than an hour ago, flag this particular folder.
    timenow = datetime.datetime.now()
    diff = (timenow - dt_latestmod)
    diff_totalseconds = diff.seconds + diff.days * 86400
    out_string = "<tr><td>"+Subfolder+"</td><td>"+str(CMloops)+"</td><td>"+str_latestmod+"</td></tr>"
    if (diff_totalseconds > 3600):
        is_running = False
    else:
        is_running = True
    out_tuple = (out_string, is_running)
    return(out_tuple)

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
    firstpart = "<p><b>This is a listing of all scenario folders</b> for run: " + cwd + ".</p>\n"
    firstpart += "<table>\n<tr><th>Scenario Folder Name</th><th>CM Loops Completed</th><th>Latest Date Modified</th></tr>\n"
    secondpart = "<p style='margin-top:60px'><b>These are the scenario folders which have not been updated in the past hour</b>. They are likely not currently running on the machine.</p>\n"
    secondpart += "<table>\n<tr><th>Scenario Folder Name</th><th>CM Loops Completed</th><th>Latest Date Modified</th></tr>\n"
    for element in ListSubfolders:
        # We split web page so that the current runs (not more than an hour ago) are displayed at the top.
        # This method is a bit hacker-ish, because we're parsing the output of SearchSubfolder instead of
        # passing a flag from SearchSubfolder.
        subfolder_tuple = SearchSubfolder(element)
        # subfolder_tuple contains two elements: [0] is the string in question, [1] is a flag indicating
        # if the scenario is running (not more than an hour ago).
        string = subfolder_tuple[0]
        is_running = subfolder_tuple[1]
        if is_running:
            firstpart += string + "\n"
        else:
            secondpart += string + "\n"
    firstpart += "</table>"
    secondpart += "</table>"
    htmlcode = firstpart + secondpart
    return(htmlcode)


### SECTION_LAUNCHER ###

# Define function for making the GAMS launching command string.
def MakeCommandString(GamsVars,settings):
    GamsOf = settings[GamsVars.index("nameattrib")] + "\\"
    GamsSFile = "s_" + settings[GamsVars.index("dpy")]
    GamsGdxf = "gdx\\" + GamsOf
    command_string_init = "gams AERESGB.gms %umul% stepsum=1 pw=255 ps=0 o=" + GamsOf + "AERESGB" + settings[1] + ".lst --of " + GamsOf + " --gdxf " + GamsGdxf + " --s_fn_base " + GamsSFile + " "
    for i in range(numvars):
        command_string_init = command_string_init + "--" + GamsVars[i] + " " + settings[i] + " "
    command_string_init = command_string_init + "> " + GamsOf + "log.txt"
    return(command_string_init)

# Initialize the launcher configs.
configlines = list()
configdata = open('config.dat', 'r')
for line in configdata:
    configlines.append(line.strip('\n'))
configdata.close()
GamsVars = configlines[0].split(',')
defaults = configlines[1].split(',')
GUIdesc = configlines[2].split(',')
if (len(GamsVars) != len(defaults) or len(defaults) != len(GUIdesc)):
    print("The number of GAMS variables, variable values, and descriptions are not the same. Abort and check GamsVars, defaults, and GUIdesc.")
    sys.exit()
numvars = len(defaults)


### SECTION_APPLICATION ###

# def updatetracker():
#     listscenfolders = SearchDir()
#     trackerhtml = ConstructMultistring(listscenfolders)

# threading.Timer(60.0,updatetracker).start()

app = Flask(__name__)

@app.route("/tracker", methods=["GET"])
def tracker():
    # threading.Timer(60.0,tracker).start()
    listscenfolders = SearchDir()
    trackerhtml = ConstructMultistring(listscenfolders)
    return(render_template("tracker.html", trackerhtml=trackerhtml))

@app.route("/launcher", methods=["GET"])
def launcher():
    configlines = list()
    configdata = open('config.dat', 'r')
    for line in configdata:
        configlines.append(line.strip('\n'))
    configdata.close()
    GamsVars = configlines[0].split(',')
    defaults = configlines[1].split(',')
    GUIdesc = configlines[2].split(',')
    if (len(GamsVars) != len(defaults) or len(defaults) != len(GUIdesc)):
        print("The number of GAMS variables, variable values, and descriptions are not the same. Abort and check GamsVars, defaults, and GUIdesc.")
        sys.exit()
    numvars = len(defaults)
    launcherhtml = ""
    for i in range(numvars):
        launcherhtml += "<dt>"+GamsVars[i]+" :: "+GUIdesc[i]+"<dd><input type='text' size='20' name='"+GamsVars[i]+"' value='"+defaults[i]+"'>"
    return(render_template("launcher.html", launcherhtml=launcherhtml))

@app.route("/launchmodel", methods=["POST"])
def launchmodel():
    settings = [None] * numvars
    for i in range(numvars):
        settings[i] = request.form[GamsVars[i]]
    GamsOf = settings[GamsVars.index("nameattrib")] + "\\"
    if not os.path.exists(GamsOf):
        os.makedirs(GamsOf)
    command_string = MakeCommandString(GamsVars,settings)
    with open('config.dat', 'w') as config:
        config.write(','.join(GamsVars) + '\n')
        config.write(','.join(settings) + '\n')
        config.write(','.join(GUIdesc))
    os.system("start cmd /K "+command_string)
    return(render_template("launchmodel.html", command_string=command_string))

@app.route("/", methods=["GET"])
def index():
    return(render_template("index.html"))

app.run(host="0.0.0.0", port=portnum)
