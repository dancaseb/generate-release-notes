# REGEX PATTERNS
# match lines that start with a + and then a # or *. Plus sign is from the diff
extract_changes_pattern = r'^\+([#*].*)'
# match ## or ### followed by a space and then a version number in [] brackets
version_headline_pattern = r'^#{2,3} (\[[0-9]+\.[0-9]+\.[0-9]+\].*) \([0-9]{4}-[0-9]{2}-[0-9]{2}\)'
# extract commit from github url
commit_pattern = r'https:\/\/.*\/commit\/([0-9a-z]*)'

delimeter_pattern = r'^\<\!\-\-Release note v[0-9]+\.[0-9]+\.[0-9]+\!\-\-\>$'

# CHANGELOG PATTERNS
commit_message_start = '* '
change_headline_start = '### '

# RELEASE NOTE PATTERNS
file_headline = '# Changelog'
section_delimeter = '***'

