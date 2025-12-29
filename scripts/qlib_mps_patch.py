#!/usr/bin/env python3
"""
Qlib MPS Support Patch

This script patches Qlib's pytorch_general_nn.py to support Apple Silicon MPS (Metal Performance Shaders).

Usage:
    python3 qlib_mps_patch.py

The patch will:
1. Add MPS device detection and selection
2. Fix GPU cache clearing to handle MPS devices
3. Add device type logging for debugging

Author: Claude Code
Date: 2025-12-28
"""

import os
import sys
import shutil
from pathlib import Path

# Qlib installation path
QLIB_PATH = Path("/opt/homebrew/Caskroom/miniconda/base/envs/Quant-env-3.11/lib/python3.11/site-packages/qlib")
TARGET_FILE = QLIB_PATH / "contrib/model/pytorch_general_nn.py"


def patch_device_selection():
    """Patch the device selection logic to support MPS"""

    # Original line 86
    original = 'self.device = torch.device("cuda:%d" % (GPU) if torch.cuda.is_available() and GPU >= 0 else "cpu")'

    # New logic with MPS support
    patched = '''# Enhanced device selection with MPS support for Apple Silicon
        if GPU is not None and GPU >= 0:
            if torch.cuda.is_available():
                self.device = torch.device("cuda:%d" % GPU)
            elif torch.backends.mps.is_available():
                self.device = torch.device("mps")
                self.logger.info("Using Apple Silicon MPS (Metal Performance Shaders) for acceleration")
            else:
                self.device = torch.device("cpu")
                self.logger.info("GPU specified but not available, using CPU")
        else:
            self.device = torch.device("cpu")'''

    return original, patched


def patch_cache_clearing():
    """Patch the GPU cache clearing to handle MPS"""

    # Original lines 331-332
    original = """if self.use_gpu:
            torch.cuda.empty_cache()"""

    # New logic that handles MPS
    patched = """# Clear GPU cache based on device type
        if self.use_gpu:
            if self.device.type == "cuda":
                torch.cuda.empty_cache()
            elif self.device.type == "mps":
                # MPS doesn't have explicit cache clearing like CUDA
                # But we can trigger garbage collection
                import gc
                gc.collect()"""

    return original, patched


def apply_patch():
    """Apply the MPS support patch to Qlib"""

    if not TARGET_FILE.exists():
        print(f"❌ Error: Qlib file not found at {TARGET_FILE}")
        print(f"Please verify your Qlib installation path.")
        sys.exit(1)

    print(f"📁 Found Qlib at: {TARGET_FILE}")

    # Read the original file
    with open(TARGET_FILE, 'r') as f:
        content = f.read()

    # Track changes
    changes_made = 0

    # Patch 1: Device selection
    original_1, patched_1 = patch_device_selection()
    if original_1 in content:
        content = content.replace(original_1, patched_1)
        changes_made += 1
        print("✅ Patched device selection logic (added MPS support)")
    else:
        print("⚠️  Device selection logic already patched or different version")

    # Patch 2: Cache clearing
    original_2, patched_2 = patch_cache_clearing()
    if original_2 in content:
        content = content.replace(original_2, patched_2)
        changes_made += 1
        print("✅ Patched GPU cache clearing (added MPS handling)")
    else:
        print("⚠️  Cache clearing logic already patched or different version")

    if changes_made == 0:
        print("\n⚠️  No changes were made. The file might already be patched.")
        return False

    # Create backup
    backup_file = TARGET_FILE.with_suffix('.py.backup_before_mps')
    shutil.copy2(TARGET_FILE, backup_file)
    print(f"📦 Backup created: {backup_file}")

    # Write patched content
    with open(TARGET_FILE, 'w') as f:
        f.write(content)

    print(f"\n✨ Successfully applied {changes_made} patch(es)!")
    print(f"🎯 Qlib now supports Apple Silicon MPS acceleration")
    print(f"\n📝 To verify the patch is working, check your training logs for:")
    print(f"   'Using Apple Silicon MPS (Metal Performance Shaders) for acceleration'")

    return True


def verify_patch():
    """Verify the patch was applied correctly"""

    print("\n🔍 Verifying patch...")

    with open(TARGET_FILE, 'r') as f:
        content = f.read()

    checks = [
        ("MPS device detection", "torch.backends.mps.is_available()"),
        ("MPS device creation", 'torch.device("mps")'),
        ("MPS cache handling", "elif self.device.type == \"mps\":"),
    ]

    all_passed = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name} - NOT FOUND")
            all_passed = False

    if all_passed:
        print("\n✅ All patches verified successfully!")
    else:
        print("\n⚠️  Some patches may not have been applied correctly")

    return all_passed


if __name__ == "__main__":
    print("=" * 70)
    print("🍎 Qlib MPS Support Patch for Apple Silicon")
    print("=" * 70)
    print()

    if apply_patch():
        verify_patch()
        print("\n" + "=" * 70)
        print("🎉 Patch installation complete!")
        print("=" * 70)
        print("\n📌 Next steps:")
        print("1. Restart your RD-Agent experiment")
        print("2. Set GPU: 0 in your config (or leave as is)")
        print("3. Check training logs for MPS confirmation")
        print("\n⚠️  Note: If you update Qlib, you'll need to reapply this patch")
        print("=" * 70)
