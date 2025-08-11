#!/usr/bin/env python3
"""
Display GTM Charts for Review
Simple script to view the generated performance charts
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
from pathlib import Path


def display_chart(chart_path, title):
    """Display a single chart"""
    if os.path.exists(chart_path):
        print(f"📊 Displaying: {title}")

        fig, ax = plt.subplots(figsize=(12, 8))
        img = mpimg.imread(chart_path)
        ax.imshow(img)
        ax.axis("off")
        ax.set_title(title, fontsize=16, fontweight="bold", pad=20)

        plt.tight_layout()
        plt.show()

        # Print file info
        file_size = os.path.getsize(chart_path) / 1024  # KB
        print(f"   📁 File: {chart_path}")
        print(f"   📏 Size: {file_size:.1f} KB")
        print(f"   ✅ Ready for GTM use\n")
    else:
        print(f"❌ Chart not found: {chart_path}")


def main():
    """Display all GTM charts"""
    print("🎨 QuantDB GTM Performance Charts Review")
    print("=" * 50)

    # Chart files and descriptions
    charts = [
        {
            "file": "quantdb_vs_akshare_performance.png",
            "title": "Main Performance Comparison (Website Hero)",
            "description": "Primary chart showing QuantDB vs AKShare performance across scenarios",
        },
        {
            "file": "quantdb_speedup_factors.png",
            "title": "Speedup Factor Visualization (Technical Docs)",
            "description": "Horizontal bar chart showing speedup multipliers",
        },
        {
            "file": "quantdb_gtm_infographic.png",
            "title": "Comprehensive GTM Infographic (Social Media)",
            "description": "Complete infographic with metrics, features, and code example",
        },
        {
            "file": "quantdb_roi_analysis.png",
            "title": "ROI & Time Savings Analysis (Business Presentations)",
            "description": "Time consumption and savings analysis for different usage levels",
        },
    ]

    # Display each chart
    for i, chart in enumerate(charts, 1):
        print(f"\n{i}. {chart['title']}")
        print(f"   📝 {chart['description']}")

        if os.path.exists(chart["file"]):
            file_size = os.path.getsize(chart["file"]) / 1024
            print(f"   ✅ Available ({file_size:.1f} KB)")
        else:
            print(f"   ❌ Missing")

    print("\n🎯 GTM Key Messages Summary:")
    print("  • Up to 99.7% performance improvement")
    print("  • Maximum 357× speedup with intelligent caching")
    print("  • Sub-50ms response times for cached data")
    print("  • Zero configuration - pip install quantdb")
    print("  • 100% AKShare API compatibility")

    print("\n📱 Recommended Usage:")
    print("  🌐 Website Hero: quantdb_vs_akshare_performance.png")
    print("  📱 Social Media: quantdb_gtm_infographic.png")
    print("  📚 Tech Docs: quantdb_speedup_factors.png")
    print("  💼 Business: quantdb_roi_analysis.png")

    print("\n📊 All charts are:")
    print("  • High resolution (300 DPI)")
    print("  • Professional styling")
    print("  • Ready for print and web")
    print("  • Consistent branding")


if __name__ == "__main__":
    main()
