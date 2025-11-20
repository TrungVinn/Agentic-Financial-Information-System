#!/usr/bin/env python3
"""
Test script for enhanced DJIA Agent features.
Tests complex queries, chart generation, and advanced analytics.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from graphs.djia_graph import run_djia_graph


def test_query(question: str, expected_features: dict):
    """Test a single query and check for expected features."""
    print(f"\n{'='*80}")
    print(f"TESTING: {question}")
    print(f"{'='*80}")
    
    try:
        result = run_djia_graph(question)
        
        # Check success
        success = result.get("success", False)
        print(f"✓ Success: {success}")
        
        # Check answer
        answer = result.get("answer", "")
        print(f"✓ Answer: {answer[:100]}..." if len(answer) > 100 else f"✓ Answer: {answer}")
        
        # Check SQL
        if result.get("sql"):
            sql_preview = result.get("sql", "")[:100]
            print(f"✓ SQL executed: {sql_preview}...")
        
        # Check dataframe
        df = result.get("df")
        if df is not None and not df.empty:
            print(f"✓ Data returned: {len(df)} rows")
        
        # Check chart
        chart = result.get("chart")
        if chart is not None:
            print(f"✓ Chart generated: Yes")
            chart_type = result.get("chart_type", "unknown")
            print(f"  - Chart type: {chart_type}")
        elif expected_features.get("needs_chart"):
            print(f"⚠ Chart expected but not generated")
        
        # Check complexity
        complexity = result.get("complexity", {})
        if complexity.get("is_multi_step"):
            print(f"✓ Multi-step query detected")
        if complexity.get("is_statistical"):
            print(f"✓ Statistical analysis detected")
        
        # Check workflow
        workflow = result.get("workflow", [])
        print(f"✓ Workflow steps: {len(workflow)}")
        for step in workflow:
            print(f"  {step['step']}. {step['description']} - {step['status']}")
        
        # Verify expected features
        print(f"\n{'Expected Features Check':^80}")
        for feature, expected in expected_features.items():
            actual = False
            if feature == "needs_chart":
                actual = chart is not None
            elif feature == "is_multi_step":
                actual = complexity.get("is_multi_step", False)
            elif feature == "is_statistical":
                actual = complexity.get("is_statistical", False)
            elif feature == "has_data":
                actual = df is not None and not df.empty
            
            status = "✓" if actual == expected else "✗"
            print(f"{status} {feature}: Expected={expected}, Actual={actual}")
        
        return success
        
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all test cases."""
    print("="*80)
    print("DJIA AGENT ENHANCEMENT TESTS")
    print("="*80)
    
    test_cases = [
        # Test 1: Simple query (baseline)
        {
            "question": "What was the closing price of Apple on March 15, 2024?",
            "expected": {
                "needs_chart": False,
                "is_multi_step": False,
                "has_data": True,
            }
        },
        
        # Test 2: Chart request - line chart
        {
            "question": "Vẽ biểu đồ giá Apple trong tháng 3 năm 2024",
            "expected": {
                "needs_chart": True,
                "is_multi_step": False,
                "has_data": True,
            }
        },
        
        # Test 3: Chart request - trend analysis
        {
            "question": "Show me the price trend of Microsoft in 2024",
            "expected": {
                "needs_chart": True,
                "is_multi_step": False,
                "has_data": True,
            }
        },
        
        # Test 4: Statistical analysis
        {
            "question": "What was the standard deviation of Apple's closing prices in 2024?",
            "expected": {
                "needs_chart": False,
                "is_multi_step": True,
                "is_statistical": True,
                "has_data": True,
            }
        },
        
        # Test 5: Advanced analytics
        {
            "question": "Calculate the median closing price of Microsoft in 2024",
            "expected": {
                "needs_chart": False,
                "is_multi_step": False,
                "has_data": True,
            }
        },
        
        # Test 6: Multi-company ranking
        {
            "question": "Rank the top 3 companies by total return in 2024",
            "expected": {
                "needs_chart": False,
                "is_multi_step": True,
                "has_data": True,
            }
        },
        
        # Test 7: Comparison query
        {
            "question": "On January 15, 2025, which company had a higher closing price, Apple or Microsoft?",
            "expected": {
                "needs_chart": False,
                "is_multi_step": False,
                "has_data": True,
            }
        },
        
        # Test 8: Aggregation
        {
            "question": "What was the average closing price of Apple during Q1 2025?",
            "expected": {
                "needs_chart": False,
                "is_multi_step": False,
                "has_data": True,
            }
        },
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\nTest {i}/{len(test_cases)}")
        success = test_query(test_case["question"], test_case["expected"])
        results.append((test_case["question"], success))
    
    # Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total} ({passed/total*100:.1f}%)")
    print("\nDetailed Results:")
    for i, (question, success) in enumerate(results, 1):
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{i}. {status}: {question[:60]}...")
    
    print("\n" + "="*80)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠ {total - passed} test(s) failed. Please review the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
