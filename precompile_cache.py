# precompile_cache.py
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import generator
import zip_exporter

def precompile():
    cache_dir = "demo_cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # 1. Activity Signup
    print("Precompiling activity_signup...")
    files_signup = generator.load_golden_example("golden_examples/activity_signup")
    zip_signup = zip_exporter.export_to_zip(files_signup)
    with open(os.path.join(cache_dir, "activity_signup.zip"), "wb") as f:
        f.write(zip_signup)
        
    # 2. Product Detail
    print("Precompiling product_detail...")
    files_detail = generator.load_golden_example("golden_examples/product_detail")
    zip_detail = zip_exporter.export_to_zip(files_detail)
    with open(os.path.join(cache_dir, "product_detail.zip"), "wb") as f:
        f.write(zip_detail)
        
    # 3. Product List
    print("Precompiling product_list...")
    files_list = generator.load_golden_example("golden_examples/product_list")
    zip_list = zip_exporter.export_to_zip(files_list)
    with open(os.path.join(cache_dir, "product_list.zip"), "wb") as f:
        f.write(zip_list)
        
    print("Precompilation complete! Zips created inside demo_cache/ directory.")

if __name__ == "__main__":
    precompile()
