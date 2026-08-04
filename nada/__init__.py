import os

PARENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
# Note, this fails with trailing slash?
ROOT_DIR_PATH = os.path.dirname(os.path.realpath(PARENT_DIR_PATH))
