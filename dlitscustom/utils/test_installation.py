import frappe
import json

def test_installation():
    """
    Test script to verify dlitscustom app installation
    Run this after installing the app to ensure everything is working correctly
    """
    try:
        print("=" * 60)
        print("🧪 Testing DLITS Custom App Installation...")
        print("=" * 60)
        
        results = {
            "workspace": False,
            "doctype": False,
            "custom_fields": False,
            "reports": False,
            "permissions": False,
            "overall": False
        }
        
        # Test 1: Workspace
        print("1️⃣ Testing workspace...")
        results["workspace"] = test_workspace()
        
        # Test 2: DocType
        print("2️⃣ Testing DocType...")
        results["doctype"] = test_doctype()
        
        # Test 3: Custom Fields
        print("3️⃣ Testing custom fields...")
        results["custom_fields"] = test_custom_fields()
        
        # Test 4: Reports
        print("4️⃣ Testing reports...")
        results["reports"] = test_reports()
        
        # Test 5: Permissions
        print("5️⃣ Testing permissions...")
        results["permissions"] = test_permissions()
        
        # Overall result
        results["overall"] = all(results.values())
        
        # Print summary
        print_test_summary(results)
        
        return results
        
    except Exception as e:
        print(f"❌ Error during installation test: {str(e)}")
        frappe.log_error(f"dlitscustom installation test error: {str(e)}", "DLITS Installation Test Error")
        return {"overall": False, "error": str(e)}

def test_workspace():
    """Test workspace creation and configuration"""
    try:
        # Check if workspace exists
        if not frappe.db.exists("Workspace", "DLITS Custom"):
            print("   ❌ Workspace 'DLITS Custom' not found")
            return False
        
        # Check workspace shortcuts
        shortcuts = frappe.db.count("Workspace Shortcut", {"parent": "DLITS Custom"})
        if shortcuts < 6:
            print(f"   ⚠️ Expected 6 shortcuts, found {shortcuts}")
            return False
        
        # Check workspace content
        workspace = frappe.get_doc("Workspace", "DLITS Custom")
        if not workspace.content:
            print("   ⚠️ Workspace content is empty")
            return False
        
        print("   ✅ Workspace test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Workspace test failed: {str(e)}")
        return False

def test_doctype():
    """Test DocType creation and configuration"""
    try:
        # Check if DocType exists
        if not frappe.db.exists("DocType", "Pricing Rule Dlits"):
            print("   ❌ DocType 'Pricing Rule Dlits' not found")
            return False
        
        # Check DocType fields
        doctype = frappe.get_doc("DocType", "Pricing Rule Dlits")
        
        # Check for key fields
        field_names = [field.fieldname for field in doctype.fields]
        required_fields = ["base_price_type", "apply_on", "discount_percentage", "discount_amount"]
        
        missing_fields = [field for field in required_fields if field not in field_names]
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
            return False
        
        # Check base price type options
        base_price_field = next((field for field in doctype.fields if field.fieldname == "base_price_type"), None)
        if not base_price_field or "Item Rate" not in base_price_field.options:
            print("   ❌ Base Price Type field missing 'Item Rate' option")
            return False
        
        print("   ✅ DocType test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ DocType test failed: {str(e)}")
        return False

def test_custom_fields():
    """Test custom fields creation"""
    try:
        # Check Sales Partner custom fields
        supplier_field = frappe.db.exists("Custom Field", {"dt": "Sales Partner", "fieldname": "supplier"})
        auto_create_field = frappe.db.exists("Custom Field", {"dt": "Sales Partner", "fieldname": "auto_create_supplier"})
        
        if not supplier_field:
            print("   ❌ Sales Partner 'supplier' field not found")
            return False
        
        if not auto_create_field:
            print("   ❌ Sales Partner 'auto_create_supplier' field not found")
            return False
        
        print("   ✅ Custom fields test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Custom fields test failed: {str(e)}")
        return False

def test_reports():
    """Test custom reports"""
    try:
        # Check if reports exist
        reports = ["Pricing Rules Analysis", "DLITS Sales Partner Commission Report"]
        
        for report in reports:
            if not frappe.db.exists("Report", report):
                print(f"   ❌ Report '{report}' not found")
                return False
        
        print("   ✅ Reports test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Reports test failed: {str(e)}")
        return False

def test_permissions():
    """Test permissions for custom doctypes"""
    try:
        # Check if DocType has permissions
        permissions = frappe.db.count("DocPerm", {"parent": "Pricing Rule Dlits"})
        
        if permissions == 0:
            print("   ❌ No permissions found for Pricing Rule Dlits")
            return False
        
        print("   ✅ Permissions test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Permissions test failed: {str(e)}")
        return False

def print_test_summary(results):
    """Print test summary"""
    try:
        print("\n" + "=" * 60)
        print("📋 INSTALLATION TEST SUMMARY")
        print("=" * 60)
        
        # Individual test results
        tests = [
            ("Workspace", results["workspace"]),
            ("DocType", results["doctype"]),
            ("Custom Fields", results["custom_fields"]),
            ("Reports", results["reports"]),
            ("Permissions", results["permissions"])
        ]
        
        for test_name, passed in tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name:<15}: {status}")
        
        print("-" * 60)
        
        # Overall result
        if results["overall"]:
            print("🎉 OVERALL RESULT: ✅ ALL TESTS PASSED")
            print("✅ DLITS Custom App is ready to use!")
            print("\n💡 Next steps:")
            print("   • Access the 'DLITS Custom' workspace")
            print("   • Create your first Pricing Rule Dlits")
            print("   • Configure Sales Partners with supplier linking")
        else:
            print("⚠️ OVERALL RESULT: ❌ SOME TESTS FAILED")
            print("🔧 Please check the failed components and reinstall if needed")
            print("\n🛠️ Troubleshooting:")
            print("   • Run: bench --site your-site-name migrate")
            print("   • Clear cache: bench --site your-site-name clear-cache")
            print("   • Restart: bench restart")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"Error printing summary: {str(e)}")

def test_pricing_rule_creation():
    """Test creating a sample pricing rule"""
    try:
        print("\n🧪 Testing Pricing Rule Creation...")
        
        # Create a test pricing rule
        test_rule = frappe.get_doc({
            "doctype": "Pricing Rule Dlits",
            "title": "Test Installation Rule",
            "base_price_type": "Price List Rate",
            "apply_on": "Item Code",
            "discount_percentage": 10,
            "enabled": 1
        })
        
        # Try to save (this will validate the doctype)
        test_rule.insert(ignore_permissions=True)
        
        # Clean up - delete the test rule
        frappe.delete_doc("Pricing Rule Dlits", test_rule.name, ignore_permissions=True)
        
        print("   ✅ Pricing rule creation test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Pricing rule creation test failed: {str(e)}")
        return False

def run_comprehensive_test():
    """Run comprehensive installation test including functionality"""
    try:
        print("🔬 Running Comprehensive Installation Test...")
        
        # Basic installation test
        basic_results = test_installation()
        
        if basic_results["overall"]:
            # Test functionality
            print("\n🔧 Testing Functionality...")
            functionality_test = test_pricing_rule_creation()
            
            if functionality_test:
                print("\n🎉 COMPREHENSIVE TEST: ✅ ALL TESTS PASSED")
                print("🚀 DLITS Custom App is fully functional!")
            else:
                print("\n⚠️ COMPREHENSIVE TEST: ❌ FUNCTIONALITY TEST FAILED")
        else:
            print("\n❌ COMPREHENSIVE TEST: Basic installation test failed")
        
        return basic_results
        
    except Exception as e:
        print(f"❌ Error in comprehensive test: {str(e)}")
        return {"overall": False, "error": str(e)}

# Utility function to run from console
def quick_test():
    """Quick test function for console use"""
    return test_installation()

if __name__ == "__main__":
    run_comprehensive_test()