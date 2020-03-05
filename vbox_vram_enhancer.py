from tkinter import *
from shutil import which

import subprocess


class VBox:
  def __init__(self, name, vram):
    self.name = name
    self.vram = vram


class VBoxManage:
  version = ''
  executable = 'VBoxManage'
  is_available = False

  def __init__(self):
    VBoxManage.version = self.get_version()
    VBoxManage.is_available = self.check_vbox()

  def check_vbox(self):
    return which(VBoxManage.executable) is not None

  def get_version(self):
    return subprocess.run([VBoxManage.executable, '--version'], stdout=subprocess.PIPE).stdout.decode('utf-8')

  def get_vms(self, only_running_vms=False, as_string=False, use_formatter=True):
    command = None
    if only_running_vms:
      command = [VBoxManage.executable, 'list', 'runningvms']
    else:
      command = [VBoxManage.executable, 'list', 'vms']
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
      subprocess.run([VBoxManage.executable, 'modifyvm', vm, '--vram', str(vram)])

  def get_vram_by_vm(self, vm):
    result = subprocess.run([VBoxManage.executable, 'showvminfo', vm], stdout=subprocess.PIPE)
    output_lines = result.stdout.decode('utf-8').splitlines()
    for line in output_lines:
      if 'VRAM size:' in line:
        vram = line.replace('VRAM size:', '').strip().replace('MB', '')
        return int(vram)


class UI:
  def __init__(self):
    pass

  def on_save(self):
    vm = self.selected_vm.get()
    vram = self.vram_slider.get()
    self.vbox.modify_vram(vm, vram)

  def on_vm_changed(self, *args):
    vm = self.selected_vm.get()
    self.vram_slider.set(self.vbox.get_vram_by_vm(vm))

  def show(self):
    self.vbox = VBoxManage()
    self.vms = self.vbox.get_offline_vms()

    self.root = Tk()
    self.root.title('VirtualBox VRAM Enhancer')

    self.frame = LabelFrame(self.root, text="Options", padx=20, pady=10)
    self.frame.grid(padx=10, pady=10, sticky=(N, S, E, W))

    self.vms_label = Label(self.frame, text='VMs:')
    self.vms_label.grid(row=0, sticky=(W))

    self.selected_vm = StringVar()
    self.selected_vm.set(self.vms[0])
    self.selected_vm.trace('w', self.on_vm_changed)

    self.vms_dropdown = OptionMenu(self.frame, self.selected_vm, *self.vms)
    self.vms_dropdown.grid(row=0, column=1, sticky=(E))

    self.vram_label = Label(self.frame, text='VRAM (MB):')
    self.vram_label.grid(row=1, sticky=(W))

    self.vram_slider = Scale(self.frame, from_=12, to=256, orient=HORIZONTAL)
    self.vram_slider.set(self.vbox.get_vram_by_vm(self.vms[0]))
    self.vram_slider.grid(row=1, column=1, sticky=(E))

    self.save_button = Button(self.frame, text='Save', command=self.on_save)
    self.save_button.grid(row=2, column=1, sticky=(E))

    self.root.mainloop()


if __name__ == "__main__":
  ui = UI()
  ui.show()