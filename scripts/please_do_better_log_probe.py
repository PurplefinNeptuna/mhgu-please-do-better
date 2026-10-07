#!/usr/bin/env python3
"""Check all default-release log formats against Forge's native buffer."""
import re
import please_do_better as recipe
from runtime_policy import check_formats
def main():
 result=check_formats();recipe.write_json(recipe.OUT/'log-tests.json',result)
 print(f"PASS: {result['checks']} log formats bounded by Forge {result['forge_buffer_bytes']}-byte buffer")
if __name__=='__main__':main()
