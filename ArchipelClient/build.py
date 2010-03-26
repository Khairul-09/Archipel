#!/usr/bin/python
# 
# build.py
# 
# Copyright (C) 2010 Antoine Mercadal <antoine.mercadal@inframonde.eu>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, commands, shutil, getopt


def usage():
    print """\
This script build Archipel GUI according to a the following set of options.
Copyright (c) 2010 Antoine Mercadal <antoine.mercadal@inframonde.eu>

Usage: build.py COMMAND [CONFIG] TARGETS [OPTIONS]

COMMAND are the following:
    --build : build the TARGETS 
    --clean : clean the TARGETS builded
    
CONFIG is the following:
    --config=Debug|Release  : configuration of the build. If ommited, default config is Release.

TARGETS are the following:
    --all           : build all. Projects and all modules;
    --project       : build only Archipel without any modules;
    --modules=list  : build a given list of module. list can be "moduleA,moduleB,moduleC" whithout blank space.
    --allmodules    : build only all modules;
    
OPTIONS are the following:
    --copymodules       : copy all the already builded modules according to TARGET to the destination dir.
    --removemodules     : remove all the builded modules according to TARGET from the destination dir.
    --generateplist     : generate a modules.plist file according to TARGET.
    --native=platform   : generate a native app. platform supported are [MacOS] (case sensitive).
    --help              : display this message

Examples:
    build all modules and generate plist:
    # build.py --build --allmodules --generateplist
    
    build only module2 in debug mode:
    # build.py --build --config=Debug --modules=module2
    
    build all project and generate native app:
    # build.py --build --all --generateplist --native=MacOS
    
    clean all:
    # build.py --clean --all
    
    clean only project, moduleA and moduleB:
    # build.py --clean --project --modules=moduleA,moduleB
"""
    sys.exit(0);


GLOBAL_LAUNCH_PATH          = commands.getoutput("pwd");
GLOBAL_BASE_PATH            = sys.path[0]
GLOBAL_MODULES_SRC_PATH     = GLOBAL_BASE_PATH + "/Modules.src/"
GLOBAL_MODULES_BUILD_PATH   = GLOBAL_BASE_PATH + "/Modules/"
GLOBAL_MODULES_PLIST_PATH   = GLOBAL_MODULES_SRC_PATH + "modules.plist";
GLOBAL_BUILD_PATH           = GLOBAL_BASE_PATH + "/Build/$CONFIG$/Archipel/*"

os.system("export PATH=/usr/local/narwhal/bin:$PATH");
os.system("cd " + GLOBAL_BASE_PATH)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "abmMcp", ["project", "all", "modules=", "allmodules", "native=", "clean", "config=", "build", "copymodules", "removemodules", "generateplist", "help"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2);
    
    opt_build_config            = "Debug";
    opt_should_build            = False;
    opt_should_copy_modules     = False;
    opt_should_remove_modules   = False;
    opt_should_generate_plist   = False;
    opt_build_only_modules      = False;
    opt_should_clean            = False;
    opt_build_native            = None;
    opt_modules_paths           = [];
    opt_build_paths             = [];
    allmodules_paths            = [];
    
    # Parses all existing modules
    for folder in os.listdir(GLOBAL_MODULES_SRC_PATH):
        if os.path.isdir(GLOBAL_MODULES_SRC_PATH + folder):
            allmodules_paths.append(GLOBAL_MODULES_SRC_PATH + folder)
            
    for o, a in opts:
        if o in ("-m", "--modules"):
            for p in a.split(","):
                opt_modules_paths.append(GLOBAL_MODULES_SRC_PATH + p)
        
        if o in ("-M", "--allmodules"):
            opt_modules_paths = allmodules_paths
        
        if o in ("-a", "--all"):
            opt_modules_paths = allmodules_paths
            opt_build_paths.append(".");
        
        if o in ("--project"):
            opt_build_paths.append(".");
        
        if o in ("-c", "--clean"):
            opt_should_clean = True;
            opt_should_build = False;
            
        if o in ("--native"):
            opt_build_native = a;
        
        if o in ("--config"):
            opt_build_config = a;
            opt_should_build = True;
        
        if o in ("--build"):
            opt_build_config = "Release";
            opt_should_build = True;
        
        if o in ("--copymodules"):
            opt_should_copy_modules = True;
        
        if o in ("--removemodules"):
            opt_should_copy_modules = False;
            opt_should_remove_modules = True;
        
        if o in ("--generateplist"):
            opt_should_generate_plist = True;
        
        if o in ("-h", "--help"):
            usage();
    
    # append any chosen modules to the build path
    opt_build_paths.extend(opt_modules_paths);
    
    if len(opt_build_paths) == 0 or (not opt_should_generate_plist and not opt_should_remove_modules and not opt_should_copy_modules and not opt_should_build and not opt_should_clean):
        print "Error: no targets specified. Use --help for usage"
        sys.exit(-1)
        
        
    # clean if asked
    if opt_should_clean:
        clean(opt_build_paths, opt_build_config)
    
    if opt_should_build:
        build(opt_build_paths, opt_build_config)
    
    if (opt_should_build and len(opt_modules_paths) > 0) or opt_should_copy_modules:
        copy_modules(opt_modules_paths, opt_build_config)
        
    if opt_should_remove_modules:
        remove_modules(opt_modules_paths, opt_build_config);
    
    if opt_build_native:
        make_native_app(opt_build_native, opt_build_config);
    
    if opt_should_generate_plist:
        generate_modules_plist(opt_modules_paths);
        
def clean(paths, config):
    for path in paths:
        build_path = path + "/Build/"
        print "# removing " + build_path
        shutil.rmtree(build_path, ignore_errors=True);
        remove_modules([path], config)

def build(paths, config):
    return_code = 0;
    
    for path in paths:
        print "# moving to " + path 
        os.chdir(path);
        
        print "# jaking..."
        return_code = os.system("export CONFIG=" + config + ";jake");
                        
        if not str(return_code) == "0":
            print "# Error in build : " + str(code)
            sys.exit("error during build")
        
        print "# Build success.";
        
        print "# get back to " + GLOBAL_BASE_PATH
        os.chdir(GLOBAL_BASE_PATH);


def copy_modules(modules_paths, config):
    for path in modules_paths:
        module_name         = path.split("/")[-1]
        module_dest_path   = GLOBAL_MODULES_BUILD_PATH + module_name;
        module_build_dir    = path + "/Build/" + config + "/" + module_name;
        
        remove_modules([path], config);
        
        print "# copying module : " + module_name 
        os.system("cp -a " + module_build_dir + " " + module_dest_path);
        
    os.system("cp " + GLOBAL_MODULES_PLIST_PATH + " " + GLOBAL_MODULES_BUILD_PATH)

def remove_modules(modules_paths, config):
    for path in modules_paths:
        module_name         = path.split("/")[-1]
        module_dest_path   = GLOBAL_MODULES_BUILD_PATH + module_name;
        module_build_dir    = path + "/Build/" + config + "/" + module_name;
        
        if os.system("rm -rf " + module_dest_path) == 0:
            print "# removed module build " + module_name


def make_native_app(platform, config):
    native_app_dir  = GLOBAL_BASE_PATH + "/NativeApplications/"+ platform +"/Archipel.app/Contents/Resources/Objective-J/Client/"
    build_dir       = GLOBAL_BUILD_PATH.replace("$CONFIG$", config)
    print build_dir;
    print "# generation of the native " + platform + " Application"
    os.chdir(GLOBAL_BASE_PATH);
    os.system("cp -a " + build_dir + " " + native_app_dir);
    os.system("cp -a "+ GLOBAL_MODULES_BUILD_PATH + " " + native_app_dir + "/Modules");
    

def generate_modules_plist(modules_paths):
    print "# Generating modules PLIST file"
    plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Modules</key>
        <array>\n"""
    
    for path in modules_paths:
        module_name         = path.split("/")[-1]
        module_cell = "            <dict>\n                <key>folder</key>\n                <string>" + module_name + "</string>\n            </dict>"
        plist += module_cell;
    
    plist +="""
        </array>
    </dict>
</plist>"""
    
    f = open(GLOBAL_MODULES_BUILD_PATH + "modules.plist", "w");
    f.write(plist);
    f.close();


if __name__ == "__main__":
    main();
