import os
#
# print(os.path.abspath(os.path.dirname(__file__)))
# print(os.path.dirname(__file__))
path = '/Users/pchang/Desktop/cloudpassage/jira_halo_issues_sync/config/etc'
# for entry in os.scandir(path):
#     print(entry.path)
print(bool(list(os.scandir(path))))