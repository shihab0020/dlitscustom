// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

frappe.query_reports["DLITS Sales Analytics"] = {
	filters: [
		{
			fieldname: "tree_type",
			label: __("Tree Type"),
			fieldtype: "Select",
			options: [
				"Customer Group",
				"Customer",
				"Supplier Group",
				"Supplier",
				"Item Group",
				"Item",
				"Territory",
				"Order Type",
				"Project",
			],
			default: "Customer",
			reqd: 1,
		},
		{
			fieldname: "doc_type",
			label: __("Based On"),
			fieldtype: "Select",
			options: [
				"All",
				"Quotation",
				"Sales Order",
				"Delivery Note",
				"Sales Invoice",
				"Sales Invoice (due)",
				"Payment Entry",
				"Purchase Order",
				"Purchase Invoice",
				"Purchase Invoice (due)",
			],
			default: "Sales Invoice",
			reqd: 1,
		},
		{
			fieldname: "value_quantity",
			label: __("Value Or Qty"),
			fieldtype: "Select",
			options: [
				"Value",
				"Quantity",
			],
			default: "Value",
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default:
				frappe.defaults.get_user_default("sales_start_date") ||
				erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default:
				frappe.defaults.get_user_default("sales_end_date") ||
				erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2],
			reqd: 1,
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: "Alejtihadat Trading Est.",
			reqd: 1,
		},
		{
			fieldname: "range",
			label: __("Range"),
			fieldtype: "Select",
			options: [
				"Weekly",
				"Monthly",
				"Quarterly",
				"Yearly",
			],
			default: "Monthly",
			reqd: 1,
		},
		{
			fieldname: "curves",
			label: __("Curves"),
			fieldtype: "Select",
			options: [
				"select",
				"all",
				"non-zeros",
				"total",
			],
			default: "total",
			reqd: 1,
		},
		{
			fieldname: "chart_type",
			label: __("Chart Type"),
			fieldtype: "Select",
			options: [
				"line",
				"bar",
				"pie",
				"doughnut",
				"area",
			],
			default: "bar",
			reqd: 1,
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			mandatory: 0,
		},
		{
			fieldname: "show_aggregate_value_from_subsidiary_companies",
			label: __("Show Aggregate Value from Subsidiary Companies"),
			fieldtype: "Check",
		},
		{
			fieldname: "additional_filters",
			label: __("Additional Filters"),
			fieldtype: "Small Text",
			default: "cost_center != 'Tax Filing - ATE' OR cost_center != 'XT-EXP - ATE'",
			css_class: "additional-filters-compact",
		},
	],
	
	onload: function(report) {
		setTimeout(() => {
			const additionalFiltersField = $(`[data-fieldname="additional_filters"] textarea`);
			if (additionalFiltersField.length) {
				additionalFiltersField.css({
					'height': '60px',
					'min-height': '60px',
					'max-height': '80px',
					'resize': 'vertical',
					'width': '100%'
				});
			}
		}, 100);
		
		this.hide_chart_tooltips();
		this.setup_chart_labels();
	},
	
	hide_chart_tooltips: function() {
		const style = document.createElement('style');
		style.textContent = `
			.chart-container .graph-svg-tip { display: none !important; }
			.chart-container .data-point-indicator { display: none !important; }
		`;
		document.head.appendChild(style);
	},
	
	format_value_plain: function(value, isCurrency) {
		// Format number without currency symbol
		const formatted = parseFloat(value).toLocaleString('en-US', {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		});
		return formatted;
	},
	
	setup_chart_labels: function() {
		const self = this;
		
		let attempts = 0;
		const checkInterval = setInterval(() => {
			attempts++;
			
			const svg = document.querySelector('.chart-container svg');
			if (svg && frappe.query_report.chart && frappe.query_report.chart.data) {
				clearInterval(checkInterval);
				console.log('✓ Chart found, adding labels');
				
				setTimeout(() => {
					self.add_permanent_labels();
					self.maintain_labels();
				}, 500);
			}
			
			if (attempts > 50) {
				clearInterval(checkInterval);
			}
		}, 200);
	},
	
	add_permanent_labels: function() {
		const chartType = frappe.query_report.get_filter_value('chart_type');
		if (chartType !== 'bar') return;
		
		const svg = document.querySelector('.chart-container svg');
		if (!svg) return;
		
		// Remove existing labels
		svg.querySelectorAll('.permanent-value-label, .permanent-value-bg, .permanent-value-shadow').forEach(el => el.remove());
		
		const valueQuantity = frappe.query_report.get_filter_value('value_quantity');
		const isCurrency = valueQuantity === 'Value';
		
		const chartData = frappe.query_report.chart.data;
		if (!chartData || !chartData.datasets || !chartData.datasets[0]) return;
		
		const values = chartData.datasets[0].values;
		const bars = svg.querySelectorAll('.dataset-units rect, .dataset-units path');
		
		console.log(`Creating perfectly centered labels for ${bars.length} bars`);
		
		let labelsCreated = 0;
		
		bars.forEach((bar, index) => {
			if (index >= values.length) return;
			
			const value = values[index];
			if (!value || parseFloat(value) === 0) return;
			
			// Get bar bounding box - use getBBox() for accurate positioning
			const bbox = bar.getBBox();
			
			// Calculate true center of the bar
			const barCenterX = bbox.x + (bbox.width / 2);
			const barTop = bbox.y;
			
			// Format value (without currency)
			const formattedValue = this.format_value_plain(value, isCurrency);
			
			// Create temporary text to measure exact width
			const tempText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
			tempText.setAttribute('font-size', '11');
			tempText.setAttribute('font-weight', 'bold');
			tempText.setAttribute('font-family', 'Arial, sans-serif');
			tempText.textContent = formattedValue;
			tempText.setAttribute('visibility', 'hidden');
			svg.appendChild(tempText);
			
			// Get exact text dimensions
			const textBBox = tempText.getBBox();
			const textWidth = textBBox.width;
			
			// Remove temporary text
			svg.removeChild(tempText);
			
			// Calculate background dimensions
			const padding = 8;
			const bgWidth = textWidth + (padding * 2);
			const bgHeight = 22;
			
			// Calculate positions - centered on the bar
			const bgX = barCenterX - (bgWidth / 2);
			const bgY = barTop - bgHeight - 8;
			
			// Add subtle drop shadow
			const shadow = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
			shadow.setAttribute('class', 'permanent-value-shadow');
			shadow.setAttribute('x', bgX + 1);
			shadow.setAttribute('y', bgY + 1);
			shadow.setAttribute('width', bgWidth);
			shadow.setAttribute('height', bgHeight);
			shadow.setAttribute('fill', 'rgba(0, 0, 0, 0.3)');
			shadow.setAttribute('rx', '4');
			shadow.setAttribute('ry', '4');
			svg.appendChild(shadow);
			
			// Create background rectangle
			const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
			bg.setAttribute('class', 'permanent-value-bg');
			bg.setAttribute('x', bgX + 50);
			bg.setAttribute('y', bgY);
			bg.setAttribute('width', bgWidth);
			bg.setAttribute('height', bgHeight);
			bg.setAttribute('fill', 'rgba(0, 0, 0, 0.75)');
			bg.setAttribute('rx', '4');
			bg.setAttribute('ry', '4');
			svg.appendChild(bg);
			
			// Create text - centered both horizontally and vertically
			const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
			text.setAttribute('class', 'permanent-value-label');
			text.setAttribute('x', barCenterX + 50);
			text.setAttribute('y', bgY + (bgHeight / 2));
			text.setAttribute('text-anchor', 'middle');
			text.setAttribute('dominant-baseline', 'central');
			text.setAttribute('font-size', '11');
			text.setAttribute('font-weight', 'bold');
			text.setAttribute('font-family', 'Arial, sans-serif');
			text.setAttribute('fill', '#ffffff');
			text.textContent = formattedValue;
			svg.appendChild(text);
			
			labelsCreated++;
			
			// Debug log
			console.log(`Bar ${index}: bbox.x=${bbox.x.toFixed(2)}, bbox.width=${bbox.width.toFixed(2)}, centerX=${barCenterX.toFixed(2)}, value=${formattedValue}`);
		});
		
		console.log(`✓ Created ${labelsCreated} perfectly centered labels`);
	},
	
	maintain_labels: function() {
		const self = this;
		
		// Re-add labels if they disappear
		setInterval(() => {
			const chartType = frappe.query_report.get_filter_value('chart_type');
			if (chartType !== 'bar') return;
			
			const svg = document.querySelector('.chart-container svg');
			if (!svg) return;
			
			const labels = svg.querySelectorAll('.permanent-value-label');
			if (labels.length === 0 && frappe.query_report.chart && frappe.query_report.chart.data) {
				console.log('Labels missing, re-adding...');
				self.add_permanent_labels();
			}
		}, 1000);
	},
	
	get_datatable_options(options) {
		const self = this;
		return Object.assign(options, {
			checkboxColumn: true,
			events: {
				onCheckRow: function (data) {
					if (!data) return;
					const data_doctype = $(data[2].html)[0].attributes.getNamedItem("data-doctype").value;
					const tree_type = frappe.query_report.filters[0].value;
					if (data_doctype != tree_type) return;

					const row_name = data[2].content;
					const raw_data = frappe.query_report.chart.data;
					const new_datasets = raw_data.datasets;
					const element_found = new_datasets.some((element, index, array) => {
						if (element.name == row_name) {
							array.splice(index, 1);
							return true;
						}
						return false;
					});
					const slice_at = { Customer: 4, Item: 5 }[tree_type] || 3;

					if (!element_found) {
						new_datasets.push({
							name: row_name,
							values: data.slice(slice_at, data.length - 1).map((column) => column.content),
						});
					}

					const new_data = {
						labels: raw_data.labels,
						datasets: new_datasets,
					};
					const new_options = Object.assign({}, frappe.query_report.chart_options, {
						data: new_data,
					});
					frappe.query_report.render_chart(new_options);

					frappe.query_report.raw_chart_data = new_data;
					
					setTimeout(() => self.add_permanent_labels(), 700);
				},
			},
		});
	},
};