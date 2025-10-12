# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class ToolsTransferDlits(Document):
	def validate(self):
		"""Validate the transfer document"""
		self.validate_qty()
		self.validate_source_and_destination()
		self.validate_stock_availability()
		self.update_status()
	
	def update_status(self):
		"""Update status based on document state"""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			self.status = "Completed"
		elif self.docstatus == 2:
			self.status = "Cancelled"
	
	def validate_qty(self):
		"""Validate quantity is positive"""
		if flt(self.qty) <= 0:
			frappe.throw("Quantity must be greater than 0")
	
	def validate_source_and_destination(self):
		"""Validate source and destination are different and properly set"""
		# Check if source fields are properly set
		if self.source_type == "Warehouse" and not self.source_warehouse:
			frappe.throw("Source Warehouse is required when Source Type is Warehouse")
		elif self.source_type == "Employee" and not self.source_employee:
			frappe.throw("Source Employee is required when Source Type is Employee")
		
		# Check if destination fields are properly set
		if self.to_type == "Warehouse" and not self.to_warehouse:
			frappe.throw("To Warehouse is required when To Type is Warehouse")
		elif self.to_type == "Employee" and not self.to_employee:
			frappe.throw("To Employee is required when To Type is Employee")
		
		# Validate warehouse belongs to company
		if self.source_type == "Warehouse" and self.source_warehouse:
			self.validate_warehouse_company(self.source_warehouse)
		
		if self.to_type == "Warehouse" and self.to_warehouse:
			self.validate_warehouse_company(self.to_warehouse)
		
		# Check if source and destination are the same
		if (self.source_type == self.to_type and
			((self.source_type == "Warehouse" and self.source_warehouse == self.to_warehouse) or
			 (self.source_type == "Employee" and self.source_employee == self.to_employee))):
			frappe.throw("Source and destination cannot be the same")
	
	def validate_warehouse_company(self, warehouse):
		"""Validate that warehouse belongs to the selected company"""
		warehouse_company = frappe.db.get_value("Warehouse", warehouse, "company")
		if warehouse_company != self.company:
			frappe.throw(f"Warehouse {warehouse} does not belong to company {self.company}")
	
	def validate_stock_availability(self):
		"""Validate stock availability for warehouse transfers - show warning for negative stock"""
		if self.source_type == "Warehouse" and self.source_warehouse:
			# Check actual stock in warehouse
			stock_qty = frappe.db.sql("""
				SELECT actual_qty
				FROM `tabBin`
				WHERE item_code = %s AND warehouse = %s
			""", (self.item, self.source_warehouse))
			
			available_qty = flt(stock_qty[0][0]) if stock_qty else 0
			
			if flt(self.qty) > available_qty:
				if not self.allow_negative_stock:
					# Require user to explicitly allow negative stock
					frappe.throw(
						f"Insufficient stock in {self.source_warehouse}. Available: {available_qty}, Required: {self.qty}. "
						f"Please check 'Allow Negative Stock' if you want to proceed with this transfer.",
						title="Insufficient Stock"
					)
				else:
					# Show warning message when negative stock is allowed
					frappe.msgprint(
						f"Warning: Transfer will result in negative stock. {self.source_warehouse} - Available: {available_qty}, Required: {self.qty}",
						title="Negative Stock Warning",
						indicator="orange"
					)
	
	def on_submit(self):
		"""Process the transfer on submit"""
		self.process_stock_transfer()
		self.update_employee_tools_allocation()
		# Update status after processing
		frappe.db.set_value(self.doctype, self.name, "status", "Completed")
	
	def on_cancel(self):
		"""Reverse the transfer on cancel"""
		self.reverse_stock_transfer()
		self.reverse_employee_tools_allocation()
		# Update status after cancellation
		frappe.db.set_value(self.doctype, self.name, "status", "Cancelled")
	
	def process_stock_transfer(self):
		"""Process stock transfer between warehouses and employees"""
		# Create stock entries only when warehouses are involved
		if self.source_type == "Warehouse" or self.to_type == "Warehouse":
			self.create_stock_entry()
		
		# Update employee tools allocation for employee transfers
		if self.source_type == "Employee" or self.to_type == "Employee":
			self.update_employee_tools_allocation()
	
	def create_stock_entry(self):
		"""Create stock entry for warehouse transfers only"""
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.posting_date = self.date
		stock_entry.company = self.company
		stock_entry.reference_doctype = self.doctype
		stock_entry.reference_docname = self.name
		
		# Allow negative stock for this stock entry
		stock_entry.allow_negative_stock = 1
		
		# Determine stock entry type and items based on transfer scenario
		if self.source_type == "Warehouse" and self.to_type == "Warehouse":
			# Warehouse to Warehouse - Material Transfer
			stock_entry.stock_entry_type = "Material Transfer"
			stock_entry.append("items", {
				"item_code": self.item,
				"qty": self.qty,
				"s_warehouse": self.source_warehouse,
				"t_warehouse": self.to_warehouse,
				"uom": self.uom,
				"allow_zero_valuation_rate": 1
			})
			
		elif self.source_type == "Warehouse" and self.to_type == "Employee":
			# Warehouse to Employee - Material Issue
			stock_entry.stock_entry_type = "Material Issue"
			stock_entry.append("items", {
				"item_code": self.item,
				"qty": self.qty,
				"s_warehouse": self.source_warehouse,
				"uom": self.uom,
				"allow_zero_valuation_rate": 1
			})
			
		elif self.source_type == "Employee" and self.to_type == "Warehouse":
			# Employee to Warehouse - Material Receipt
			stock_entry.stock_entry_type = "Material Receipt"
			stock_entry.append("items", {
				"item_code": self.item,
				"qty": self.qty,
				"t_warehouse": self.to_warehouse,
				"uom": self.uom,
				"allow_zero_valuation_rate": 1
			})
		
		try:
			stock_entry.insert()
			stock_entry.submit()
			
			# Link the stock entry to this transfer using db.set_value to avoid document save issues
			frappe.db.set_value(self.doctype, self.name, "stock_entry", stock_entry.name)
			frappe.db.commit()
			
		except Exception as e:
			frappe.throw(f"Error creating stock entry: {str(e)}")
	
	def update_employee_tools_allocation(self):
		"""Update employee tools allocation records"""
		# Reduce from source employee
		if self.source_type == "Employee":
			self.update_employee_allocation(self.source_employee, -flt(self.qty))
		
		# Add to destination employee
		if self.to_type == "Employee":
			self.update_employee_allocation(self.to_employee, flt(self.qty))
	
	def update_employee_allocation(self, employee, qty_change):
		"""Update or create employee tools allocation record"""
		# Check if allocation record exists
		allocation = frappe.db.exists("Employee Tools Allocation", {
			"employee": employee,
			"item": self.item
		})
		
		if allocation:
			# Update existing allocation
			current_qty = frappe.db.get_value("Employee Tools Allocation", allocation, "allocated_qty")
			new_qty = flt(current_qty) + flt(qty_change)
			
			if new_qty < 0:
				frappe.throw(f"Cannot reduce tools allocation below zero for employee {employee}")
			
			frappe.db.set_value("Employee Tools Allocation", allocation, "allocated_qty", new_qty)
		else:
			# Create new allocation record if qty_change is positive
			if flt(qty_change) > 0:
				allocation_doc = frappe.new_doc("Employee Tools Allocation")
				allocation_doc.employee = employee
				allocation_doc.item = self.item
				allocation_doc.allocated_qty = flt(qty_change)
				allocation_doc.allocation_date = self.date
				allocation_doc.insert()
			else:
				frappe.throw(f"No existing allocation found for employee {employee} and item {self.item}")
	
	def reverse_stock_transfer(self):
		"""Reverse stock transfer on cancel"""
		# Cancel linked stock entry if exists (only for warehouse transfers)
		if self.stock_entry:
			stock_entry_doc = frappe.get_doc("Stock Entry", self.stock_entry)
			if stock_entry_doc.docstatus == 1:
				stock_entry_doc.cancel()
	
	def reverse_employee_tools_allocation(self):
		"""Reverse employee tools allocation on cancel"""
		# Reverse the allocation changes only for employee transfers
		if self.source_type == "Employee":
			self.update_employee_allocation(self.source_employee, flt(self.qty))
		
		if self.to_type == "Employee":
			self.update_employee_allocation(self.to_employee, -flt(self.qty))

