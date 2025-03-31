Version History:
~~~~~~~~~~~~~~~~

-  1.8.8: Respect the ``verify`` flag in ``syncup``

-  1.8.7: Loosen system encoding check on Windows

-  1.8.6: Fix progress file path for concurrent runs by @Bluetea577

-  1.8.5: Workaround Baidu returning 200 for invalid/expired
   ``access_token`` so that ``refresh_token()`` continues to work

-  1.8.4: Fix packing error (missing ‘auth.json’)

-  1.8.3: Fix upload getting 31023 - ‘Param Error’

-  1.8.2: Remove invalid GPL text

-  1.8.1: Fix multiprocess (by changing all ``__foo()`` to ``_foo()``)

-  1.8: No longer server auth

-  1.7.14: Fix issue #612: Can’t download file when a directory has more
   than 1000 items

-  1.7.13: Correct the Aliyun auth server address

-  1.7.12: Fix deps in setup.py

-  1.7.11: Fix jsonload() bug introduced in the previous commit

-  1.7.10: Make sure progress json loading error handling works in both
   Json 2 and 3

-  1.7.9: Fix multiprocess file writing

-  1.7.8: Fix package reading

-  1.7.7: Enable local auth using env vars

-  1.7.6: Fix ``refresh_token``

-  1.7.5: Restore recursive directory walk

-  1.7.4: Screwed up ``refresh_token``

-  1.7.3: Make ``list`` able to handle more than 1000 items

-  1.7.2: Fix release.sh

-  1.7.1: Fix upgrading in Python2 (unicode file name support seems to
   be broken)

-  1.7.0: Follow Baidu’s encrypted MD5 algorithm

-  1.6.11: Revert the previous change - Baidu PCS’s behavior is wrong
   and makes no sense

-  1.6.10: Fix MD5 comparison (thanks to @shenchucheng)

-  1.6.9: Make auth server list dynamic

-  1.6.8: Fix 1000 items limit for downloading

-  1.6.7: Handle update check network exceptions

-  1.6.6: Let it cry when dies, so we can have some trace

-  1.6.5: Fix ``KeyError: u'md5'`` in remote directory walking

-  1.6.4: Fix ``--move`` argument causing exception

-  1.6.3: Change default timeout to 5 minutes

-  1.6.2: Properly handle (treat it as no error) error_code 31061 (file
   already exists) from PCS

-  1.6.1: Ensure cache loading/saving failures won’t affect normal
   operations; Fix the bug that clean up code not called on exit

-  1.6.0: Fix 1000 items limit for remote directory listing

-  1.5.13: Fix multiprocess upload/syncup missing some files

-  1.5.12: Add one more heroku server; Workaround “ValueError: unknown
   locale: UTF-8” on macOS (by xslidian)

-  1.5.11: Fix typo near version string

-  1.5.10: Print the error code if the action failed

-  1.5.9: Migrate the OpenShift auth server

-  1.5.8: Add ``--move`` flag to delete source files/directories on
   successfull transfers

-  1.5.7: Reduce multiprocess timeout to 49 days, to accommodate Python
   3 on Windows

-  1.5.6: Downloading using downloader also retries

-  1.5.5: Minor: Improve ‘multiprocess’ installation prompts

-  1.5.4: Print instructions on how to fix ‘multiprocess’ errors

-  1.5.3: Change to streaming upload

-  1.5.2: Defuse the circular import bomb brought in the previous
   version…

-  1.5.1: Improve multiprocess (and fix filter() for Python3)

-  1.5.0: Multi-Process for directory download / upload / sync up/down

-  1.4.4: Aria2 download works even file names contain single quote (’)

-  1.4.3: Fix \__server_auth()

-  1.4.2: Add bypy version in getting and refresshing token requests for
   finer control

-  1.4.1: Fix a severe bug in token refreshing

-  1.4.0: Correct Refresh server list; Add in update check

-  1.3.9: Add in queue for capturing JSONs returned from PCS

-  1.3.8: Don’t output Auth Server failures if no ``-d`` specified

-  1.3.7: Allow passing leading dash arguments to downloader

-  1.3.6: Fix downdir downloads to a wrong directory structure

-  1.3.5: Fix aria2 unable to resume download

-  1.3.4: Add –select-fastest-mirror, –config-dir command line
   arguments; Switch to wheel dist format

-  1.3.3: Fix the upload failure when slices expired

-  1.3.2: Enable SSL check by default now

-  1.3.1: Fix setup.py failures

-  1.3.0: Major change: Make bypy a real Python package

-  1.2.22: Fix “TypeError: b’xxxxxx’ is not JSON serializable” for cache

-  1.2.21: Support aria2 downloading resuming (disable preallocation)

-  1.2.20: Fix an error in upload resuming; Add in retries for aria2

-  1.2.19: Add in aria2 download support

-  1.2.18: Add in upload resuming using slices; Fix Unicode issues with
   ``py2_jsondump()``; Fix the pypi setup package

-  1.2.17: Fix UnicodeEncodeError on redirect; Add in retry on urllib3
   TimeOutError

-  1.2.16: Add in proxy prompts

-  1.2.15: Fix a severe bug (accidental directory deletion) in
   ``download`` command intoduced in 1.2.14

-  1.2.14: Add in ``download`` command

-  1.2.13: Remove argcomplete; Improve encoding handling prompting

-  1.2.12: Add in (optional) argcomplete

-  1.2.11: Fix Exception in error dump introduced in 1.2.10

-  1.2.10: Handle (32, ‘EPIPE’); Warn LOUDLY on encoding failures;
   Remove ``is_revision``

-  1.2.9: Fix formatex() Syntax Error; Handle (110, ‘ETIMEDOUT’)

-  1.2.8: Fix a Syntax Error; Handle
   ``{'error_code': 0, 'error_msg': 'no error'``}

-  1.2.7: Fix Hash Cache JSON saving (need to use string for Hashes)

-  1.2.6: Fix Hash Cache JSON dumping (``Unicode`` again)

-  1.2.5: Add in offline (cloud) download; Fix stack printing

-  1.2.4: Fix command line parsing for Python 3 (``Unicode`` by default)

-  1.2.3: Fix GUI for Python 3

-  1.2.2: Fix division for Python 3

-  1.2.1: Make it ``universal`` (Python 2 & 3 compatible)

-  1.0.20: Initial release
