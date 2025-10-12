# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class EmployeeToolsAllocation(Document):
	def validate(self):
		"""Validate the allocation document"""
		self.validate_qty()
		self.update_last_updated()
	
	def validate_qty(self):
		"""Validate quantity is not negative"""
		if self.allocated_qty < 0:
			frappe.throw("Allocated quantity cannot be negative")
	
	def update_last_updated(self):
		"""Update the last updated timestamp"""
		self.last_updated = now()
	
	def before_save(self):
		"""Update last updated timestamp before saving"""
		self.update_last_updated()