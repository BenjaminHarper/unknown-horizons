# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################
import horizons.main
from storage import PositiveSizedSlotStorage
from horizons.util import WorldObject, WeakList, NamedObject
from tradepost import TradePost

class Settlement(TradePost, NamedObject):
	"""The Settlement class describes a settlement and stores all the necessary information
	like name, current inhabitants, lists of tiles and houses, etc belonging to the village."""
	def __init__(self, owner):
		"""
		@param owner: Player object that owns the settlement
		"""
		super(Settlement, self).__init__()
		self.buildings = WeakList() # List of all the buildings belonging to the settlement
		self.__init(owner)

	def __init(self, owner, tax_setting=1.0):
		self.owner = owner
		self.tax_setting = tax_setting
		self.setup_storage()

	def get_default_name(self):
		return horizons.main.db("SELECT name FROM data.citynames WHERE for_player = 1 ORDER BY random() LIMIT 1")[0][0]

	@property
	def inhabitants(self):
		"""Returns number of inhabitants (sum of inhabitants of its buildings)"""
		return sum([building.inhabitants for building in self.buildings])

	def setup_storage(self):
		self.inventory = PositiveSizedSlotStorage(0)
		self.inventory.add_change_listener(self._changed)

	def get_building(self, point):
		"""Returns the building at the position (x, y)
		@param point: position to look at
		@return: Building class instance or None if none is found.
		"""
		for b in self.buildings:
			if b.position.contains(point):
				return b
		else:
			return None

	def save(self, db, islandid):
		super(Settlement, self).save(db)

		db("INSERT INTO settlement (rowid, island, owner, tax_setting) VALUES(?, ?, ?, ?)",
			self.getId(), islandid, self.owner.getId(), self.tax_setting)
		self.inventory.save(db, self.getId())

	@classmethod
	def load(cls, db, worldid):
		self = cls.__new__(cls)

		super(Settlement, self).load(db, worldid)

		owner, tax = db("SELECT owner, tax_setting FROM settlement WHERE rowid = ?", worldid)[0]
		self.__init(WorldObject.get_object_by_id(owner), tax)

		self.inventory.load(db, worldid)

		# load all buildings from this settlement
		# the buildings will expand the area of the settlement by adding everything,
		# that is in the radius of the building, to the settlement.
		self.buildings = WeakList()
		for building_id, building_type in \
				db("SELECT rowid, type FROM building WHERE location = ?", worldid):
			buildingclass = horizons.main.session.entities.buildings[building_type]
			buildingclass.load(db, building_id)

		return self
