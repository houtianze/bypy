### Version History:

- 1.3.2: Enable SSL check by default now
- 1.3.1: Fix setup.py failures
- 1.3.0: Major change: Make bypy a real Python package

---
- 1.2.22: Fix "TypeError: b'xxxxxx' is not JSON serializable" for cache
- 1.2.21: Support aria2 downloading resuming (disable preallocation)
- 1.2.20: Fix an error in upload resuming; Add in retries for aria2
- 1.2.19: Add in aria2 download support
- 1.2.18: Add in upload resuming using slices; Fix Unicode issue with py2_jsondump(); Fix the pypi setup package
- 1.2.17: Fix UnicodeEncodeError on redirect; Add in retry on urllib3 TimeOutError
- 1.2.16: Add in proxy prompts
- 1.2.15: Fix a severe bug (accidental directory deletion) in `download` command intoduced in 1.2.14
- 1.2.14: Add in `download` command
- 1.2.13: Remove argcomplete; Improve encoding handling prompting
- 1.2.12: Add in (optional) argcomplete
- 1.2.11: Fix Exception in error dump introduced in 1.2.10
- 1.2.10: Handle (32, 'EPIPE'); Warn LOUDLY on encoding failures; Remove 'is_revision'
- 1.2.9: Fix formatex() Syntax Error; Handle (110, 'ETIMEDOUT')
- 1.2.8: Fix a Syntax Error; Handle {'error_code': 0, 'error_msg': 'no error'}
- 1.2.7: Fix Hash Cache JSON saving (need to using string for Hashes)
- 1.2.6: Fix Hash Cache JSON dumping (`Unicode` again)
- 1.2.5: Add in offline (cloud) download; Fix stack printing
- 1.2.4: Fix command line parsing for Python 3 (`Unicode` by default)
- 1.2.3: Fix GUI for Python 3
- 1.2.2: Fix division for Python 3
- 1.2.1: Make it `universal` (Python 2 & 3 compatible)
- 1.0.20: Initial release

