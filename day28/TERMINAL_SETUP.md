# Terminal Setup for God Agent

## UTF-8 Encoding Issues

If you encounter `UnicodeDecodeError` when using the chat interface, follow these steps:

### macOS Terminal Setup

1. **Check current locale:**
   ```bash
   locale
   ```

2. **Set UTF-8 locale (temporary):**
   ```bash
   export LC_ALL=en_US.UTF-8
   export LANG=en_US.UTF-8
   ```

3. **Set UTF-8 locale (permanent):**

   Add to `~/.zshrc` (or `~/.bash_profile` if using bash):
   ```bash
   export LC_ALL=en_US.UTF-8
   export LANG=en_US.UTF-8
   ```

   Then reload:
   ```bash
   source ~/.zshrc
   ```

4. **Verify encoding:**
   ```bash
   python3 -c "import sys; print(sys.stdin.encoding)"
   ```

   Should output: `UTF-8`

### Alternative: Use Environment Variables

Run chat.py with explicit encoding:
```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 python chat.py
```

### iTerm2 Users

1. Go to **Preferences → Profiles → Terminal**
2. Set "Character Encoding" to **UTF-8**
3. Restart iTerm2

### VS Code Terminal Users

Add to settings.json:
```json
{
  "terminal.integrated.env.osx": {
    "LC_ALL": "en_US.UTF-8",
    "LANG": "en_US.UTF-8"
  }
}
```

## Cleanup Issues on Exit

If you see `RuntimeError` messages when exiting, this is expected and harmless. The application properly cleans up MCP connections, but some async cleanup warnings may appear. These can be safely ignored.

## Quick Test

Test your encoding setup:
```bash
python3 -c "import locale; print(locale.getpreferredencoding())"
```

Should output: `UTF-8`

## Still Having Issues?

Try running with explicit Python encoding:
```bash
PYTHONIOENCODING=utf-8 python chat.py
```
