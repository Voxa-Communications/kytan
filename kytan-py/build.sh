pip uninstall -y kytan-py

echo "Building"
#rm dist
python -m pip install build twine
#cd kvprocessor
python -m build
# Find the most recent .whl file in the dist directory
WHEEL_FILE=$(ls -t dist/*.whl | head -n 1)

# Check if a wheel file was found
if [ -z "$WHEEL_FILE" ]; then
    echo "Error: No .whl file found in dist directory"
    exit 1
fi

# Install the most recent wheel file
echo "Installing $WHEEL_FILE"
python -m pip install --force-reinstall --no-build-isolation "$WHEEL_FILE"