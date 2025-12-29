#!/usr/bin/env python3
"""
Qlib MPS Verification Script

This script verifies that MPS (Metal Performance Shaders) is working correctly
with the patched Qlib installation.

Usage:
    python3 verify_mps.py
"""

import sys
import torch

print("=" * 70)
print("🔍 Qlib MPS Verification")
print("=" * 70)
print()

# Check PyTorch version
print(f"PyTorch Version: {torch.__version__}")
print()

# Check CUDA
print("CUDA Status:")
if torch.cuda.is_available():
    print(f"  ✅ Available: {torch.version.cuda}")
    print(f"  📱 Device: {torch.cuda.get_device_name(0)}")
else:
    print(f"  ❌ Not Available (this is normal on macOS)")
print()

# Check MPS
print("MPS (Apple Silicon) Status:")
if hasattr(torch.backends, 'mps'):
    is_built = torch.backends.mps.is_built()
    is_available = torch.backends.mps.is_available()
    print(f"  🔧 Built: {is_built}")
    print(f"  ✅ Available: {is_available}")

    if is_available:
        print()
        print("🧪 Testing MPS device...")
        try:
            # Test basic tensor operations on MPS
            device = torch.device("mps")
            x = torch.randn(1000, 100).to(device)
            y = torch.randn(100, 1000).to(device)
            z = torch.mm(x, y)

            print(f"  ✅ Tensor operations successful!")
            print(f"  📊 Shape: {z.shape}")

            # Test model training on MPS
            print()
            print("🧪 Testing model training on MPS...")
            model = torch.nn.Linear(100, 10).to(device)
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

            # Simulate training step
            optimizer.zero_grad()
            output = model(x[:, :100])
            loss = output.sum()
            loss.backward()
            optimizer.step()

            print(f"  ✅ Training step successful!")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            print(f"  ⚠️  MPS may not be working correctly")
    else:
        print(f"  ⚠️  MPS not available - check if you're on Apple Silicon")
else:
    print(f"  ❌ MPS not supported in this PyTorch version")

print()

# Check Qlib patch
print("Qlib Patch Status:")
try:
    import qlib
    from qlib.contrib.model.pytorch_general_nn import GeneralPTNN
    import inspect

    # Get the source code
    source_file = inspect.getsourcefile(GeneralPTNN)
    print(f"  📁 File: {source_file}")

    with open(source_file, 'r') as f:
        content = f.read()

    # Check for MPS support
    mps_checks = [
        ("MPS detection", "torch.backends.mps.is_available()"),
        ("MPS device", 'torch.device("mps")'),
        ("MPS cache handling", 'self.device.type == "mps"'),
    ]

    all_ok = True
    for check_name, check_str in mps_checks:
        if check_str in content:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name} - NOT FOUND")
            all_ok = False

    if all_ok:
        print()
        print("✅ Qlib is patched with MPS support!")
    else:
        print()
        print("⚠️  Qlib MPS patch not found or incomplete")
        print("   Run: python3 scripts/qlib_mps_patch.py")

except ImportError as e:
    print(f"  ❌ Cannot import Qlib: {e}")
except Exception as e:
    print(f"  ❌ Error checking Qlib: {e}")

print()
print("=" * 70)
print("✅ Verification Complete!")
print("=" * 70)
print()

# Summary
print("📋 Summary:")
if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    print("  🎯 Your Mac supports MPS acceleration")
    print("  ⚡ GPU: GPU should be set to 0 in config")
    print("  🚀 Expected speedup: 3-5x faster than CPU")
else:
    print("  ⚠️  MPS not available on this system")
    print("  🐢 Training will use CPU (slower but stable)")
