# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe import _, scrub
from frappe.query_builder import DocType
from frappe.query_builder.functions import IfNull
from frappe.utils import add_days, add_to_date, flt, getdate

from erpnext.accounts.utils import get_fiscal_year


def execute(filters=None):
	filters = frappe._dict(filters or {})
	# Special report showing all doctype totals on a single chart; overrides some filters
	if filters.doc_type == "All":
		filters.tree_type = "Customer"
		filters.value_quantity = "Value"
		filters.curves = "total"
		output = None
		for dt in [
			"Quotation",
			"Sales Order",
			"Delivery Note",
			"Sales Invoice",
			"Sales Invoice (due)",
			"Payment Entry",
			"Purchase Order",
			"Purchase Invoice",
			"Purchase Invoice (due)",
		]:
			filters.doc_type = dt
			output = append_report(dt, output, Analytics(filters).run())
		return output
	else:
		return Analytics(filters).run()


def append_report(dt, org, new):
	# idx 1 is data, 3 is chart
	new[1].insert(0, {"entity": dt})  # heading
	new[1].append({})  # empty row
	# datasets can be an empty list if no dates are supplied by the Dashboard Chart
	if not new[3]["data"]["datasets"]:
		new[3]["data"]["datasets"].append({"name": None, "values": []})
	new[3]["data"]["datasets"][0]["name"] = dt  # override curve name
	if org:
		org[1].extend(new[1])
		org[3]["data"]["datasets"].extend(new[3]["data"]["datasets"])
		return org
	else:
		return new


class Analytics:
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.data = []  # Initialize data attribute
		self.validate_tree_type_and_doc_type()
		if self.filters.doc_type == "Payment Entry" and self.filters.value_quantity == "Quantity":
			frappe.throw(_("Only Value available for Payment Entry"))
		self.date_field = (
			"transaction_date"
			if self.filters.doc_type in ["Quotation", "Sales Order", "Purchase Order"]
			else "due_date"
			if self.filters.doc_type in ["Sales Invoice (due)", "Purchase Invoice (due)"]
			else "posting_date"
		)
		if self.filters.doc_type and self.filters.doc_type.startswith("Sales Invoice"):
			self.filters.doc_type = "Sales Invoice"
		elif self.filters.doc_type and self.filters.doc_type.startswith("Purchase Invoice"):
			self.filters.doc_type = "Purchase Invoice"
		self.months = [
			"Jan",
			"Feb",
			"Mar",
			"Apr",
			"May",
			"Jun",
			"Jul",
			"Aug",
			"Sep",
			"Oct",
			"Nov",
			"Dec",
		]
		self.get_period_date_ranges()

	def validate_tree_type_and_doc_type(self):
		"""Validate that tree type and document type are compatible"""
		sales_tree_types = ["Customer", "Customer Group"]
		purchase_tree_types = ["Supplier", "Supplier Group"]
		neutral_tree_types = ["Item", "Item Group", "Territory", "Order Type", "Project"]

		sales_doc_types = ["Quotation", "Sales Order", "Delivery Note", "Sales Invoice", "Sales Invoice (due)"]
		purchase_doc_types = ["Purchase Order", "Purchase Invoice", "Purchase Invoice (due)"]
		neutral_doc_types = ["Payment Entry", "All"]

		tree_type = self.filters.get("tree_type")
		doc_type = self.filters.get("doc_type")

		if not tree_type or not doc_type:
			return  # Let normal validation handle required fields

		# Check for incompatible combinations
		if tree_type in sales_tree_types and doc_type in purchase_doc_types:
			frappe.throw(_("Tree Type '{0}' is not compatible with Document Type '{1}'. Please select a Sales document type.").format(tree_type, doc_type))

		if tree_type in purchase_tree_types and doc_type in sales_doc_types:
			frappe.throw(_("Tree Type '{0}' is not compatible with Document Type '{1}'. Please select a Purchase document type.").format(tree_type, doc_type))

		# Special validations
		if tree_type == "Order Type" and doc_type not in ["Quotation", "Sales Order", "Purchase Order"]:
			frappe.throw(_("Tree Type 'Order Type' is only compatible with Quotation, Sales Order, and Purchase Order."))

		if tree_type == "Project" and doc_type == "Quotation":
			frappe.throw(_("Tree Type 'Project' is not compatible with Document Type 'Quotation'."))

	def update_company_list_for_parent_company(self):
		company_list = [self.filters.get("company")]

		selected_company = self.filters.get("company")
		if (
			selected_company
			and self.filters.get("show_aggregate_value_from_subsidiary_companies")
			and frappe.db.get_value("Company", selected_company, "is_group")
		):
			lft, rgt = frappe.db.get_value("Company", selected_company, ["lft", "rgt"])
			child_companies = frappe.db.get_list(
				"Company", filters={"lft": [">", lft], "rgt": ["<", rgt]}, pluck="name"
			)

			company_list.extend(child_companies)

		self.filters["company"] = company_list

	def run(self):
		self.update_company_list_for_parent_company()
		self.get_columns()
		self.get_data()
		self.get_chart_data()

		# Skipping total row for tree-view reports
		skip_total_row = 0

		if self.filters.tree_type in ["Supplier Group", "Item Group", "Customer Group", "Territory"]:
			skip_total_row = 1

		return self.columns, self.data, None, self.chart, None, skip_total_row

	def get_columns(self):
		self.columns = [
			{
				"label": _(self.filters.tree_type),
				"options": self.filters.tree_type if self.filters.tree_type != "Order Type" else "",
				"fieldname": "entity",
				"fieldtype": "Link" if self.filters.tree_type != "Order Type" else "Data",
				"width": 140 if self.filters.tree_type != "Order Type" else 200,
			}
		]
		if self.filters.tree_type in ["Customer", "Supplier", "Item"]:
			self.columns.append(
				{
					"label": _(self.filters.tree_type + " Name"),
					"fieldname": "entity_name",
					"fieldtype": "Data",
					"width": 140,
				}
			)

		if self.filters.tree_type == "Item":
			self.columns.append(
				{
					"label": _("UOM"),
					"fieldname": "stock_uom",
					"fieldtype": "Link",
					"options": "UOM",
					"width": 100,
				}
			)

		for end_date in self.periodic_daterange:
			period = self.get_period(end_date)
			self.columns.append(
				{"label": _(period), "fieldname": scrub(period), "fieldtype": "Float", "width": 120}
			)

		self.columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Float", "width": 120})

	def get_data(self):
		if self.filters.tree_type in ["Customer", "Supplier"]:
			self.get_sales_transactions_based_on_customers_or_suppliers()
			self.get_rows()

		elif self.filters.tree_type == "Item":
			if self.filters.doc_type == "Payment Entry":
				self.data = []
				return
			self.get_sales_transactions_based_on_items()
			self.get_rows()

		elif self.filters.tree_type in ["Customer Group", "Supplier Group", "Territory"]:
			if self.filters.doc_type == "Payment Entry":
				self.data = []
				return
			self.get_sales_transactions_based_on_customer_or_territory_group()
			self.get_rows_by_group()

		elif self.filters.tree_type == "Item Group":
			if self.filters.doc_type == "Payment Entry":
				self.data = []
				return
			self.get_sales_transactions_based_on_item_group()
			self.get_rows_by_group()

		elif self.filters.tree_type == "Order Type":
			if self.filters.doc_type not in ["Quotation", "Sales Order", "Purchase Order"]:
				self.data = []
				return
			self.get_sales_transactions_based_on_order_type()
			self.get_rows_by_group()

		elif self.filters.tree_type == "Project":
			if self.filters.doc_type in ["Quotation"]:
				self.data = []
				return
			self.get_sales_transactions_based_on_project()
			self.get_rows()

	def get_sales_transactions_based_on_order_type(self):
		if self.filters.get("value_quantity") == "Value":
			value_field = "base_net_total"
		else:
			value_field = "total_qty"

		doctype = DocType(self.filters.doc_type)

		query = (
			frappe.qb.from_(doctype)
			.select(
				doctype.order_type.as_("entity"),
				doctype[self.date_field],
				doctype[value_field].as_("value_field"),
			)
			.where(
				(doctype.docstatus == 1)
				& (doctype.company.isin(self.filters.company))
				& (doctype[self.date_field].between(self.filters.from_date, self.filters.to_date))
				& (IfNull(doctype.order_type, "") != "")
			)
		)

		# Add cost center filter if provided
		if self.filters.get("cost_center"):
			query = query.where(doctype.cost_center == self.filters.cost_center)

		# Add additional filters if provided
		if self.filters.get("additional_filters"):
			additional_conditions = self.parse_additional_filters()
			for condition in additional_conditions:
				query = query.where(condition)

		self.entries = query.orderby(doctype.order_type).run(as_dict=True)

		self.get_teams()

	def get_sales_transactions_based_on_customers_or_suppliers(self):
		if self.filters.get("value_quantity") == "Value":
			value_field = "base_net_total as value_field"
		else:
			value_field = "total_qty as value_field"

		if self.filters.tree_type == "Customer":
			entity_name = "customer_name as entity_name"
			if self.filters.doc_type == "Quotation":
				entity = "party_name as entity"
			elif self.filters.doc_type == "Payment Entry":
				entity = "party as entity"
				entity_name = "party_name as entity_name"
				value_field = "base_received_amount as value_field"
			else:
				entity = "customer as entity"
		else:
			entity_name = "supplier_name as entity_name"
			if self.filters.doc_type == "Payment Entry":
				entity = "party as entity"
				entity_name = "party_name as entity_name"
				value_field = "base_paid_amount as value_field"
			else:
				entity = "supplier as entity"

		# Use frappe.qb for complex queries with additional filters
		doctype = DocType(self.filters.doc_type)

		query = (
			frappe.qb.from_(doctype)
			.select(
				doctype[entity.split(" as ")[0]].as_("entity"),
				doctype[entity_name.split(" as ")[0]].as_("entity_name"),
				doctype[value_field.split(" as ")[0]].as_("value_field"),
				doctype[self.date_field],
			)
			.where(
				(doctype.docstatus == 1)
				& (doctype.company.isin(self.filters.company))
				& (doctype[self.date_field].between(self.filters.from_date, self.filters.to_date))
			)
		)

		# Add cost center filter if provided
		if self.filters.get("cost_center"):
			query = query.where(doctype.cost_center == self.filters.cost_center)

		# Add additional filters if provided
		if self.filters.get("additional_filters"):
			additional_conditions = self.parse_additional_filters()
			if additional_conditions:
				# For multiple conditions, we need to handle OR logic properly
				# frappe.qb supports OR through the | operator
				if len(additional_conditions) == 1:
					query = query.where(additional_conditions[0])
				else:
					# Combine conditions with OR
					combined_condition = additional_conditions[0]
					for condition in additional_conditions[1:]:
						combined_condition = combined_condition | condition
					query = query.where(combined_condition)

		if self.filters.doc_type in ["Sales Invoice", "Purchase Invoice", "Payment Entry"]:
			query = query.where(doctype.is_opening == "No")

		self.entries = query.run(as_dict=True)

		self.entity_names = {}
		for d in self.entries:
			self.entity_names.setdefault(d.entity, d.entity_name)

	def get_sales_transactions_based_on_items(self):
		if self.filters.get("value_quantity") == "Value":
			value_field = "base_net_amount"
		else:
			value_field = "stock_qty"

		doctype = DocType(self.filters.doc_type)
		doctype_item = DocType(f"{self.filters.doc_type} Item")

		query = (
			frappe.qb.from_(doctype_item)
			.join(doctype)
			.on(doctype.name == doctype_item.parent)
			.select(
				doctype_item.item_code.as_("entity"),
				doctype_item.item_name.as_("entity_name"),
				doctype_item.stock_uom,
				doctype_item[value_field].as_("value_field"),
				doctype[self.date_field],
			)
			.where(
				(doctype_item.docstatus == 1)
				& (doctype.company.isin(self.filters.company))
				& (doctype[self.date_field].between(self.filters.from_date, self.filters.to_date))
			)
		)

		# Add cost center filter if provided
		if self.filters.get("cost_center"):
			query = query.where(doctype.cost_center == self.filters.cost_center)

		# Add additional filters if provided
		if self.filters.get("additional_filters"):
			additional_conditions = self.parse_additional_filters()
			if additional_conditions:
				# For multiple conditions, we need to handle OR logic properly
				# frappe.qb supports OR through the | operator
				if len(additional_conditions) == 1:
					query = query.where(additional_conditions[0])
				else:
					# Combine conditions with OR
					combined_condition = additional_conditions[0]
					for condition in additional_conditions[1:]:
						combined_condition = combined_condition | condition
					query = query.where(combined_condition)

		self.entries = query.run(as_dict=True)

		self.entity_names = {}
		for d in self.entries:
			self.entity_names.setdefault(d.entity, d.entity_name)

	def get_sales_transactions_based_on_customer_or_territory_group(self):
		if self.filters.get("value_quantity") == "Value":
			value_field = "base_net_total as value_field"
		else:
			value_field = "total_qty as value_field"

		if self.filters.tree_type == "Customer Group":
			entity_field = "customer_group as entity"
		elif self.filters.tree_type == "Supplier Group":
			entity_field = "supplier as entity"
			self.get_supplier_parent_child_map()
		else:
			entity_field = "territory as entity"

		doctype = DocType(self.filters.doc_type)

		query = (
			frappe.qb.from_(doctype)
			.select(
				doctype[entity_field.split(" as ")[0]].as_("entity"),
				doctype[value_field.split(" as ")[0]].as_("value_field"),
				doctype[self.date_field],
			)
			.where(
				(doctype.docstatus == 1)
				& (doctype.company.isin(self.filters.company))
				& (doctype[self.date_field].between(self.filters.from_date, self.filters.to_date))
			)
		)

		# Add cost center filter if provided
		if self.filters.get("cost_center"):
			query = query.where(doctype.cost_center == self.filters.cost_center)

		# Add additional filters if provided
		if self.filters.get("additional_filters"):
			additional_conditions = self.parse_additional_filters()
			if additional_conditions:
				# For multiple conditions, we need to handle OR logic properly
				# frappe.qb supports OR through the | operator
				if len(additional_conditions) == 1:
					query = query.where(additional_conditions[0])
				else:
					# Combine conditions with OR
					combined_condition = additional_conditions[0]
					for condition in additional_conditions[1:]:
						combined_condition = combined_condition | condition
					query = query.where(combined_condition)

		if self.filters.doc_type in ["Sales Invoice", "Purchase Invoice", "Payment Entry"]:
			query = query.where(doctype.is_opening == "No")

		self.entries = query.run(as_dict=True)
		self.get_groups()

	def get_sales_transactions_based_on_item_group(self):
		if self.filters.get("value_quantity") == "Value":
			value_field = "base_net_amount"
		else:
			value_field = "qty"

		doctype = DocType(self.filters.doc_type)
		doctype_item = DocType(f"{self.filters.doc_type} Item")

		query = (
			frappe.qb.from_(doctype_item)
			.join(doctype)
			.on(doctype.name == doctype_item.parent)
			.select(
				doctype_item.item_group.as_("entity"),
				doctype_item[value_field].as_("value_field"),
				doctype[self.date_field],
			)
			.where(
				(doctype_item.docstatus == 1)
				& (doctype.company.isin(self.filters.company))
				& (doctype[self.date_field].between(self.filters.from_date, self.filters.to_date))
			)
		)

		# Add cost center filter if provided
		if self.filters.get("cost_center"):
			query = query.where(doctype.cost_center == self.filters.cost_center)

		# Add additional filters if provided
		if self.filters.get("additional_filters"):
			additional_conditions = self.parse_additional_filters()
			if additional_conditions:
				# For multiple conditions, we need to handle OR logic properly
				# frappe.qb supports OR through the | operator
				if len(additional_conditions) == 1:
					query = query.where(additional_conditions[0])
				else:
					# Combine conditions with OR
					combined_condition = additional_conditions[0]
					for condition in additional_conditions[1:]:
						combined_condition = combined_condition | condition
					query = query.where(combined_condition)

		self.entries = query.run(as_dict=True)

		self.get_groups()

	def get_sales_transactions_based_on_project(self):
		if self.filters.get("value_quantity") == "Value":
			value_field = "base_net_total as value_field"
		else:
			value_field = "total_qty as value_field"

		if self.filters.doc_type == "Payment Entry":
			if self.filters.tree_type == "Customer":
				value_field = "base_received_amount as value_field"
			else:
				value_field = "base_paid_amount as value_field"

		doctype = DocType(self.filters.doc_type)

		query = (
			frappe.qb.from_(doctype)
			.select(
				doctype.project.as_("entity"),
				doctype[value_field.split(" as ")[0]].as_("value_field"),
				doctype[self.date_field],
			)
			.where(
				(doctype.docstatus == 1)
				& (doctype.company.isin(self.filters.company))
				& (doctype.project != "")
				& (doctype[self.date_field].between(self.filters.from_date, self.filters.to_date))
			)
		)

		# Add cost center filter if provided
		if self.filters.get("cost_center"):
			query = query.where(doctype.cost_center == self.filters.cost_center)

		# Add additional filters if provided
		if self.filters.get("additional_filters"):
			additional_conditions = self.parse_additional_filters()
			if additional_conditions:
				# For multiple conditions, we need to handle OR logic properly
				# frappe.qb supports OR through the | operator
				if len(additional_conditions) == 1:
					query = query.where(additional_conditions[0])
				else:
					# Combine conditions with OR
					combined_condition = additional_conditions[0]
					for condition in additional_conditions[1:]:
						combined_condition = combined_condition | condition
					query = query.where(combined_condition)

		if self.filters.doc_type in ["Sales Invoice", "Purchase Invoice", "Payment Entry"]:
			query = query.where(doctype.is_opening == "No")

		self.entries = query.run(as_dict=True)

	def get_rows(self):
		self.data = []
		self.get_periodic_data()

		for entity, period_data in self.entity_periodic_data.items():
			row = {
				"entity": entity,
				"entity_name": self.entity_names.get(entity) if hasattr(self, "entity_names") else None,
			}
			total = 0
			for end_date in self.periodic_daterange:
				period = self.get_period(end_date)
				amount = flt(period_data.get(period, 0.0))
				row[scrub(period)] = amount
				total += amount

			row["total"] = total

			if self.filters.tree_type == "Item":
				row["stock_uom"] = period_data.get("stock_uom")

			self.data.append(row)

	def get_rows_by_group(self):
		self.get_periodic_data()
		out = []

		for d in reversed(self.group_entries):
			row = {"entity": d.name, "indent": self.depth_map.get(d.name)}
			total = 0
			for end_date in self.periodic_daterange:
				period = self.get_period(end_date)
				amount = flt(self.entity_periodic_data.get(d.name, {}).get(period, 0.0))
				row[scrub(period)] = amount
				if d.parent and (self.filters.tree_type != "Order Type" or d.parent == "Order Types"):
					self.entity_periodic_data.setdefault(d.parent, frappe._dict()).setdefault(period, 0.0)
					self.entity_periodic_data[d.parent][period] += amount
				total += amount

			row["total"] = total
			out = [row, *out]

		self.data = out

	def get_periodic_data(self):
		self.entity_periodic_data = frappe._dict()

		for d in self.entries:
			if self.filters.tree_type == "Supplier Group":
				d.entity = self.parent_child_map.get(d.entity)
			period = self.get_period(d.get(self.date_field))
			self.entity_periodic_data.setdefault(d.entity, frappe._dict()).setdefault(period, 0.0)
			self.entity_periodic_data[d.entity][period] += flt(d.value_field)

			if self.filters.tree_type == "Item":
				self.entity_periodic_data[d.entity]["stock_uom"] = d.stock_uom

	def get_period(self, posting_date):
		if self.filters.range == "Weekly":
			period = _("Week {0} {1}").format(str(posting_date.isocalendar()[1]), str(posting_date.year))
		elif self.filters.range == "Monthly":
			period = _(str(self.months[posting_date.month - 1])) + " " + str(posting_date.year)
		elif self.filters.range == "Quarterly":
			period = _("Quarter {0} {1}").format(
				str(((posting_date.month - 1) // 3) + 1), str(posting_date.year)
			)
		else:
			year = get_fiscal_year(posting_date, company=self.filters.company[0])
			period = str(year[0])
		return period

	def get_period_date_ranges(self):
		from dateutil.relativedelta import MO, relativedelta

		from_date, to_date = getdate(self.filters.from_date), getdate(self.filters.to_date)

		increment = {"Monthly": 1, "Quarterly": 3, "Half-Yearly": 6, "Yearly": 12}.get(self.filters.range, 1)

		if self.filters.range in ["Monthly", "Quarterly"]:
			from_date = from_date.replace(day=1)
		elif self.filters.range == "Yearly":
			from_date = get_fiscal_year(from_date)[1]
		else:
			from_date = from_date + relativedelta(from_date, weekday=MO(-1))

		self.periodic_daterange = []
		for _dummy in range(1, 53):
			if self.filters.range == "Weekly":
				period_end_date = add_days(from_date, 6)
			else:
				period_end_date = add_to_date(from_date, months=increment, days=-1)

			if period_end_date > to_date:
				period_end_date = to_date

			self.periodic_daterange.append(period_end_date)

			from_date = add_days(period_end_date, 1)
			if period_end_date == to_date:
				break

	def get_groups(self):
		if self.filters.tree_type == "Territory":
			parent = "parent_territory"
		if self.filters.tree_type == "Customer Group":
			parent = "parent_customer_group"
		if self.filters.tree_type == "Item Group":
			parent = "parent_item_group"
		if self.filters.tree_type == "Supplier Group":
			parent = "parent_supplier_group"

		self.depth_map = frappe._dict()

		self.group_entries = frappe.db.sql(
			f"""select name, lft, rgt , {parent} as parent
			from `tab{self.filters.tree_type}` order by lft""",
			as_dict=1,
		)

		for d in self.group_entries:
			if d.parent:
				self.depth_map.setdefault(d.name, self.depth_map.get(d.parent) + 1)
			else:
				self.depth_map.setdefault(d.name, 0)

	def get_teams(self):
		self.depth_map = frappe._dict()

		self.group_entries = frappe.db.sql(
			f""" select * from (select "Order Types" as name, 0 as lft,
			2 as rgt, '' as parent union select distinct order_type as name, 1 as lft, 1 as rgt, "Order Types" as parent
			from `tab{self.filters.doc_type}` where ifnull(order_type, '') != '') as b order by lft, name
		""",
			as_dict=1,
		)

		for d in self.group_entries:
			if d.parent:
				self.depth_map.setdefault(d.name, self.depth_map.get(d.parent) + 1)
			else:
				self.depth_map.setdefault(d.name, 0)

	def get_supplier_parent_child_map(self):
		self.parent_child_map = frappe._dict(
			frappe.db.sql(""" select name, supplier_group from `tabSupplier`""")
		)

	def parse_additional_filters(self):
		"""Parse additional filters string into frappe.qb conditions"""
		if not self.filters.get("additional_filters"):
			return []

		filter_string = self.filters.additional_filters.strip()
		if not filter_string:
			return []

		conditions = []
		# Split by AND/OR operators (case insensitive)
		import re
		parts = re.split(r'\s+(and|or)\s+', filter_string, flags=re.IGNORECASE)

		i = 0
		while i < len(parts):
			part = parts[i].strip()
			if part.lower() in ['and', 'or']:
				i += 1
				continue

			# Parse individual condition
			condition = self.parse_single_condition(part)
			if condition:
				conditions.append(condition)
			i += 1

		# Debug: Print parsed conditions
		# frappe.msgprint(f"Parsed {len(conditions)} conditions from filter: {filter_string}")
		# for idx, cond in enumerate(conditions):
		# 	frappe.msgprint(f"Condition {idx+1}: {cond}")

		return conditions

	def parse_single_condition(self, condition_str):
		"""Parse a single condition like 'cost_center != "Main Cost Center"'"""
		import re

		# Match patterns like field operator value
		pattern = r'^(\w+)\s*([!=<>]+|like|not like|in|not in)\s*(.+)$'
		match = re.match(pattern, condition_str.strip(), re.IGNORECASE)

		if not match:
			return None

		field, operator, value = match.groups()
		field = field.strip()
		operator = operator.strip().lower()
		value = value.strip()

		# Handle quoted values
		if value.startswith('"') and value.endswith('"'):
			value = value[1:-1]
		elif value.startswith("'") and value.endswith("'"):
			value = value[1:-1]

		# Map operators to frappe.qb operators
		doctype = DocType(self.filters.doc_type)
		field_obj = doctype[field]

		if operator == '==':
			return field_obj == value
		elif operator == '!=':
			return field_obj != value
		elif operator == '<':
			return field_obj < value
		elif operator == '<=':
			return field_obj <= value
		elif operator == '>':
			return field_obj > value
		elif operator == '>=':
			return field_obj >= value
		elif operator == 'like':
			return field_obj.like(value)
		elif operator == 'not like':
			return field_obj.not_like(value)
		elif operator == 'in':
			# Parse comma-separated values
			values = [v.strip().strip('"\'') for v in value.split(',')]
			return field_obj.isin(values)
		elif operator == 'not in':
			# Parse comma-separated values
			values = [v.strip().strip('"\'') for v in value.split(',')]
			return field_obj.notin(values)

		return None


	def get_chart_data(self):
		length = len(self.columns)

		if self.filters.tree_type in ["Customer", "Supplier"]:
			labels = [d.get("label") for d in self.columns[2 : length - 1]]
		elif self.filters.tree_type == "Item":
			labels = [d.get("label") for d in self.columns[3 : length - 1]]
		else:
			labels = [d.get("label") for d in self.columns[1 : length - 1]]

		datasets = []
		if self.filters.curves != "select":
			for curve in self.data:
				data = {
					"name": curve.get("entity_name", curve["entity"]),
					"values": [curve[scrub(label)] for label in labels],
				}
				if self.filters.curves == "non-zeros" and not sum(data["values"]):
					continue
				elif self.filters.curves == "total" and "indent" in curve:
					if curve["indent"] == 0:
						datasets.append(data)
				elif self.filters.curves == "total":
					if datasets:
						a = [
							data["values"][idx] + datasets[0]["values"][idx]
							for idx in range(len(data["values"]))
						]
						datasets[0]["values"] = a
					else:
						datasets.append(data)
						datasets[0]["name"] = _("Total")
				else:
					datasets.append(data)
		else:
			# When curves is "select", show all data by default
			for curve in self.data[:10]:  # Show top 10 entries
				data = {
					"name": curve.get("entity_name", curve["entity"]),
					"values": [curve[scrub(label)] for label in labels],
				}
				if sum(data["values"]) > 0:  # Only include if there's actual data
					datasets.append(data)

		# Get chart type from filters, default to line
		chart_type = self.filters.get("chart_type", "line")

		# Build chart configuration
		self.chart = {
			"data": {"labels": labels, "datasets": datasets},
			"type": chart_type,
			"chart_options": {}  # Add chart_options key for JS to populate
		}

		if self.filters.get("value_quantity") == "Value":
			self.chart["fieldtype"] = "Currency"
		else:
			self.chart["fieldtype"] = "Float"