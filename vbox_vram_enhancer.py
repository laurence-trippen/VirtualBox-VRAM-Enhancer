from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from shutil import which
from pathlib import Path

import os
import subprocess
import json


class Config():
  virtualbox_path = ''
  directory = os.path.join(str(Path.home()), 'VBoxVRAMEnhancer')
  path = os.path.join(directory, 'config.json')

  @staticmethod
  def check():
    existed = True

    if not os.path.exists(Config.directory):
      os.makedirs(Config.directory)
      existed = False

    if not os.path.isfile(Config.path):
      data = {
        'virtualbox_path': ''
      }
      Config.save(data)
      existed = False
    
    return existed

  @staticmethod
  def save(data):
    with open(Config.path, "w") as outfile:
      json.dump(data, outfile, indent=4)

  @staticmethod
  def load():
    with open(Config.path) as json_file:
      data = json.load(json_file)
      Config.virtualbox_path = data['virtualbox_path']


class VBoxManage:
  path = ''
  executable = 'VBoxManage.exe'

  def __init__(self):
    pass

  def is_available(self):
    return which(os.path.join(VBoxManage.path)) is not None

  def get_version(self):
    return subprocess.run([VBoxManage.path, '--version'], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

  def get_vms(self, only_running_vms=False, as_string=False, use_formatter=True):
    command = None
    if only_running_vms:
      command = [VBoxManage.path, 'list', 'runningvms']
    else:
      command = [VBoxManage.path, 'list', 'vms']
    result = subprocess.run(command, stdout=subprocess.PIPE)
    if as_string == True:
      return result.stdout.decode('utf-8')
    else:
      if use_formatter:
        names = result.stdout.decode('utf-8').splitlines()
        formatted_names = []
        for name in names:
          formatted_names.append(self.format_vm_name(name))
        return formatted_names
      else:
        return result.stdout.decode('utf-8').splitlines()

  def format_vm_name(self, name, uuid=False):
    name = name.split()
    if not uuid:
      return name[0].replace('"', '')
    else:
      return name[1]

  def get_offline_vms(self):
    vms = self.get_vms()
    running_vms = self.get_vms(only_running_vms=True)
    offline_vms = []
    for vm in vms:
      if not vm in running_vms:
        offline_vms.append(vm)
    return offline_vms

  def modify_vram(self, vm, vram):
    if vram >= 12 and vram <= 256:
      subprocess.run([VBoxManage.path, 'modifyvm', vm, '--vram', str(vram)])

  def get_vram_by_vm(self, vm):
    result = subprocess.run([VBoxManage.path, 'showvminfo', vm], stdout=subprocess.PIPE)
    output_lines = result.stdout.decode('utf-8').splitlines()
    for line in output_lines:
      if 'VRAM size:' in line:
        vram = line.replace('VRAM size:', '').strip().replace('MB', '')
        return int(vram)


class TkApp(Frame):
  def __init__(self, master=None):
    Frame.__init__(self, master)
    self.vbox = VBoxManage()
    self.check_vbox_path()
    self.vms = self.vbox.get_offline_vms()

    self.frame = LabelFrame(master, text='Options', padx=20, pady=10)
    self.frame.grid(padx=10, pady=10, sticky=N+S+E+W)

    self.vms_label = Label(self.frame, text='VMs:')
    self.vms_label.grid(row=0, sticky=(W))

    self.selected_vm = StringVar()
    self.selected_vm.set(self.vms[0])
    self.selected_vm.trace('w', self.on_vm_changed)

    self.vms_dropdown = OptionMenu(self.frame, self.selected_vm, *self.vms)
    self.vms_dropdown.grid(row=0, column=1, sticky=(E))

    self.vram_label = Label(self.frame, text='VRAM (MB):', pady=10)
    self.vram_label.grid(row=1, sticky=(W), pady=(10, 10))

    self.vram_slider = Scale(self.frame, from_=12, to=256, orient=HORIZONTAL)
    self.vram_slider.set(self.vbox.get_vram_by_vm(self.vms[0]))
    self.vram_slider.grid(row=1, column=1, sticky=(E))

    self.save_button = Button(self.frame, text='Save', command=self.on_save)
    self.save_button.grid(row=2, column=1, sticky=(E))

    self.statusbar = Label(master, text='VirtualBox ' + self.vbox.get_version(), bd=1, relief=SUNKEN)
    self.statusbar.grid(columnspan=2, sticky=(W, S, E))
      
  def check_vbox_path(self, save_if_available=False):
    if self.vbox.is_available():
      if save_if_available:
        Config.save({ 'virtualbox_path': VBoxManage.path })
    else:
      should_vbox_set = messagebox.askokcancel('VirtualBox not found.','Please choose the VirtualBox Directory')
      
      if should_vbox_set: 
        VBoxManage.path = filedialog.askdirectory(title="Choose VirtualBox Directory")
        VBoxManage.path += os.sep + VBoxManage.executable

        self.check_vbox_path(save_if_available=True)
      else:
        self.destroy()
        exit()

  def on_save(self):
    vm = self.selected_vm.get()
    vram = self.vram_slider.get()
    self.vbox.modify_vram(vm, vram)

  def on_vm_changed(self, *args):
    vm = self.selected_vm.get()
    self.vram_slider.set(self.vbox.get_vram_by_vm(vm))


def main():
  config_exists = Config.check()
  if config_exists:
    Config.load()
    VBoxManage.path = Config.virtualbox_path

  root = Tk()
  root.title('VirtualBox VRAM Enhancer')
  root.geometry('320x200')
  root.columnconfigure(0, weight=1)
  root.rowconfigure(0, weight=1)
  app = TkApp(master=root)
  app.mainloop()


if __name__ == '__main__':
  main()