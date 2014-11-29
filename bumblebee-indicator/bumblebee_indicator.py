#!/usr/bin/python
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

import os

try:
  from gi.repository import AppIndicator3 as AppIndicator
except ImportError:
  from gi.repository import AppIndicator

from gi.repository import Gtk, GLib, Notify

BBSWITCH_INTERFACE = "/proc/acpi/bbswitch"

# Inspired by previous, legacy work, as well as
# https://bitbucket.org/cpbotha/indicator-cpuspeed/src/6f172c5d57082757034d4df49ab77072495117f8/indicator-cpuspeed.py?at=default


class BumblebeeIndicator(object):
  def __init__(self):
    self.indicator = AppIndicator.Indicator.new_with_path(
      "bumblebee-indicator",
      "bumblebee-indicator",
      AppIndicator.IndicatorCategory.HARDWARE,
      os.path.join(os.path.dirname(os.path.realpath(__file__)), "icons")
    )

    self.indicator.set_icon_full("bumblebee-indicator-inactive", "Discrete graphics card is inactive")
    self.indicator.set_attention_icon_full("bumblebee-indicator-active", "Discrete graphics card is active")

    self.menu = Gtk.Menu()

    self.card_state_menu_item = Gtk.MenuItem()
    self.card_state_menu_item.set_sensitive(False)
    self.card_state_menu_item.show()
    self.menu.append(self.card_state_menu_item)

    separator = Gtk.SeparatorMenuItem()
    separator.show()
    self.menu.append(separator)

    item = Gtk.MenuItem()
    item.set_label("Exit")
    item.connect("activate", self.handler_menu_exit)
    item.show()
    self.menu.append(item)

    self.menu.show()
    self.indicator.set_menu(self.menu)

    self.state = self.check_for_card_state()
    self.card_state_change(self.state)

    Notify.init("bumblebee-indicator")
    self.notification = None

    # not ideal
    GLib.timeout_add_seconds(4, self.handler_timeout)

  def handler_timeout(self):
    state = self.check_for_card_state()
    self.card_state_change(state)
    return True

  def check_for_card_state(self):
    if not os.path.exists(BBSWITCH_INTERFACE):
      return "NONE"

    with open(BBSWITCH_INTERFACE, "r") as f:
      data = f.read().strip()

    if "ON" in data:
      return "ON"

    if "OFF" in data:
      return "OFF"

  def card_state_change(self, new_state):
    new_state = new_state.upper()
    text = "Graphics card: {}".format(new_state)
    self.card_state_menu_item.set_label(text)
    if new_state == "ON":
      indicator_state = AppIndicator.IndicatorStatus.ATTENTION
    else:
      indicator_state = AppIndicator.IndicatorStatus.ACTIVE

    self.indicator.set_status(indicator_state)

    if self.state != new_state:
      self.state = new_state
      self.notification = Notify.Notification.new("Bumblebee", text, "dialog-information")
      self.notification.show()
      # until https://bugs.launchpad.net/ubuntu/+source/notify-osd/+bug/390508
      # is fixed, this doesn't work
      # self.notification.set_timeout(0.5)

  def handler_menu_exit(self, evt):
    Gtk.main_quit()

  def main(self):
    Gtk.main()

if __name__ == "__main__":
    indicator = BumblebeeIndicator()
    indicator.main()
