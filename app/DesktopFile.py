#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
#
# This file is part of bumblebee-ui.
#
# bumblebee-ui is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# bumblebee-ui is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with bumblebee-ui. If not, see <http://www.gnu.org/licenses/>.
#
### END LICENSE

#TODO Use inheritance of object programming language to simplify the code

import os
# A wonderful xdg support module that Lekensteyn introduce to me: the ui is now based on the xdg standards.
import xdg.Menu
#TODO : Find a better way to import xdg abilities
from xdg.DesktopEntry import *

# TODO : Get rid of all config except the one in model files and .cfg file
# TODO : Find the best way to configure desktop files : use MODEL desktop file to check the mode, and set the files.

import Config

data_dirs=xdg.BaseDirectory.xdg_data_dirs
data_home=xdg.BaseDirectory.xdg_data_home
modes=Config.mode_keys

class GetDesktop():
    def __init__(self, entry, category=None):
        self.desktop_file_id = list(entry.DesktopFileID.rsplit('.')) + [category]
        if self.desktop_file_id[1] == 'desktop' :
              self.desktopEntry= entry.DesktopEntry

    #DESKTOP ENTRY PARSE TO DETERMINE STATES
    def isLocal(self):
        if data_home in self.desktopEntry.getFileName(): return True
    
    def isConfigured(self):
        """Function to check if the desktop file is configured for Bumblebee or not"""
        if self.isLocal() \
        and self.desktopEntry.get(key='X-Ayatana-Desktop-Shortcuts') \
        and self.desktopEntry.get(key='Exec', group='BumblebeeDisable Shortcut Group') \
        and self.desktopEntry.get(key='Exec', group='BumblebeeEnable Shortcut Group'):    
            return True
        else : return False

    #DESKTOP ENTRY VALUE PARSING
    def getConfiguredEntry(self):
        return [ self.desktopEntry.getName(), 
            self.desktopEntry.get(key='Exec',group='BumblebeeEnable Shortcut Group').split(' ')]
    
    def getInfo(self):
        self.entry_info=[self.desktopEntry.getName().encode("utf-8") , 
                         self.desktop_file_id[0].encode("utf-8") , 
                         self.desktop_file_id[2] , 
                         self.desktopEntry.getIcon().encode("utf-8")]
        if self.isConfigured(): 
            return self.entry_info + self.getConfiguredInfo()
        else : return self.entry_info + [True] + 4*[False] + ['default']

    def getConfiguredInfo(self):
        """Function to get configuration from a configured desktop entry : 
        Is Application, Configured, (Selected by default : unselected), Mode, 32bits, Compression
        """
        entry_common = 3*[True]
        entry_exec= self.desktopEntry.getExec()
        shortcuts= self.desktopEntry.get(key='X-Ayatana-Desktop-Shortcuts')
        exec_config= self.getExecConfig(entry_exec)
        if 'optirun ' in entry_exec: 
            if ('BumblebeeEnable' in shortcuts and exec_config[0]):
                return entry_common + [modes['perf']] + exec_config[1:]
            elif ('BumblebeeDisable' in shortcuts and not exec_config[0]):
                return entry_common + [modes['eco']] + exec_config[1:]
        elif (not 'optirun ' in entry_exec and 'BumblebeeDisable' in shortcuts):
            exec_config=self.getExecConfig(self.desktopEntry.get(key='Exec', group='BumblebeeDisable Shortcut Group'))
            return entry_common + [modes['option']] + exec_config[1:]
        else : return entry_common + ['Unrecognized mode'] + exec_config[1:]
			
    def setTrue( arg, next_arg=None): return {arg:True}
    
    def getCompression( arg, next_arg=None, default=Config.default_compression): 
        if (next_arg in Config.compression_list and next_arg != default): return {arg:next_arg}
    
    def getExecConfig(self, Exec, i=-1, 
        case={'-32':setTrue, '-f':setTrue, '-c':getCompression},
        skip=['optirun', 'ecoptirun', '-d', ':0', ':1', ':2'] + Config.compression_list):
        """Function to search for configuration inside optirun arguments in the desktop file object : 
        Force_eco, 32bits, Compression"""
        arg_list=Exec.split(' ')	
        exec_config={'-f':False, '-32':False, '-c':'default'}
        for arg in arg_list:
            i = i+1
            if arg in case: exec_config.update(case.get(arg)(arg,next_arg=arg_list[i+1]))
            elif arg in skip: continue
            else: break
        return [exec_config['-f']] + [exec_config['-32']] + [exec_config['-c']]


class SetDesktop:
    def __init__(self, fileid):
        self.entry= DesktopEntry()
        filepath = '/applications/' + fileid + '.desktop'
        self.local_path=data_home+filepath
        #Use os.path.exists here because you already need it and DesktopEntry use it !
        try :
            self.entry.parse(data_home + filepath)
            self.local=True
        except xdg.Exceptions.ParsingError:  
            for data_dir in reversed(data_dirs):
                try : 
                    self.entry.parse(data_dir + filepath)
                except xdg.Exceptions.ParsingError:
                    continue 
            self.local=False

    #DESKTOP ENTRY BASE CONFIGURATION
    def setEntry(self):
        entry_name=self.entry.getName()
        if self.local:
            self.setShortcuts()
            print "User entry file configured for bumblebee : " + entry_name
        else : 
            self.setEntryComment()
            self.setShortcuts()
            print "File copied, tagged and configured for bumblebee : " + entry_name
        print self.local_path
        self.entry.write(self.local_path)

    def setShortcuts(self):
        self.setShortcutKey()
        self.cmd=self.entry.get(key="Exec")
        self.setShortcutGroup('Launch without Bumblebee', self.cmd)
        self.setShortcutGroup('Launch with Bumblebee', \
                              "optirun -f " + self.cmd, \
                              "BumblebeeDisable")
    
    def setShortcutKey(self, key='X-Ayatana-Desktop-Shortcuts', value=['BumblebeeDisable','BumblebeeEnable'] ):
        try : 
            shortcuts=self.entry.get(key)
            if not (value[0] or value[1]) in shortcuts:
                self.entry.set(key, value[0] +';' + shortcuts)
            elif value[1] in shortcuts:
                self.entry.set(key, shortcuts.replace(value[1],value[0]))
        except : self.entry.set(key, value[0])

    def setShortcutGroup(self, name, cmd, \
                                 shortcut="BumblebeeEnable"):
        group=self.getShortcutGroup(shortcut)
        self.entry.addGroup(group)
        self.entry.set("Name", name, group)
        self.entry.set("Exec", cmd, group)
        self.entry.set("TargetEnvironment", "Unity;GNOME;KDE;", group)
        
    def getShortcutGroup(self,shortcut):
        #return '{0} {1}'.format(shortcut,group))
        return "%s Shortcut Group" % shortcut
        
    def setEntryComment(self, tag="File created by bumblebee-ui"):
        comment_value= self.entry.get("Comment",locale=False)
        if comment_value : tagged_value= comment_value + "(%s)" % tag
        else : tagged_value=tag
        self.entry.set("Comment", tagged_value ,locale=False)
        
    def setOptirun(self, mode, bits32, compression):
        self.Exec=self.entry.get("Exec", group=self.getShortcutGroup('BumblebeeEnable'), list=True)
        option=list()
        if bits32 : option.append("-32")
        if compression : option.append("-c " + compression) 
        if mode == modes['perf']:
            self.setOptirunKeys(['optirun','-f'] + option, \
                                [], \
                                ['BumblebeeEnable','BumblebeeDisable'])
        elif mode == modes['eco']:
            self.setOptirunKeys(['optirun'] + option, \
                                ['optirun','-f'] + option, \
                                ['BumblebeeDisable','BumblebeeEnable'])
        elif mode == modes['option']:
            self.setOptirunKeys([], 
                                ['optirun','-f'] + option, \
                                ['BumblebeeDisable','BumblebeeEnable'])
        self.writeEntry()
	
    def setOptirunKeys(self, Exec, ShortcutExec, ShortcutList):
        self.setExec(Exec)
        self.setShortcutKey(self, value=ShortcutList)
        self.setExec(ShortcutExec, self.getShortcutGroup(ShortcutList[0]))

    def setExec(self, values, shortcut=None):
        self.entry.set("Exec", " ".join(values + self.Exec), group=shortcut)

    def isCreated(self, tag="File created by bumblebee-ui"):
        try :
            if tag in self.entry.get("Comment",locale=False) : return True
        except : return False
        
    def unsetEntry(self):
		entry_name=self.entry.getName()
        if self.isCreated():
            os.remove(self.local_path)
            print "File created by bumblebee-ui removed : " + entry_name
        else : 
            self.unsetShortcuts()
            self.writeEntry()
            print "Entry modified by bumblebee-ui unconfigured : " + entry_name

    def unsetShortcuts (self, shortcuts=['BumblebeeDisable','BumblebeeEnable']):
        self.unsetShortcutKey()
        for shortcut in shortcuts : self.unsetShortcutGroup(shortcut)

    def unsetShortcutGroup(self, shortcut):
        self.entry.removeGroup(self.getShortcutGroup(shortcut))

    def unsetShortcutKey(self, key='X-Ayatana-Desktop-Shortcuts', value=['BumblebeeDisable','BumblebeeEnable'] ):
        shortcuts=self.entry.get(key, list=True)
        #TODO Change by a list comprehension
        for matching_value in value :
            if matching_value in shortcuts:
                shortcuts.remove(matching_value)
        if len(shortcuts)==0: self.entry.removeKey(key)
        else : self.entry.set(key, ';'.join(shortcuts))

    def writeEntry(self):     
        try : 
            #self.entry.validate()
            self.entry.write(self.local_path)
        except ValidationError, e:
            print e
            #print 'The file to write is not valid : %s' % self.entry

#TODO Write a new class : to get the configuration inside the MODEL desktop files
#class BumblebeeModelDesktop:
#    def __init__(self,filename):
#        self.model = 