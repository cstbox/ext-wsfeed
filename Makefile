# CSTBox framework
#
# Makefile for building the Debian distribution package containing the
# extension for feeding variable values from an external application.
#
# author = Eric PASCUAL - CSTB (eric.pascual@cstb.fr)

# name of the CSTBox module
MODULE_NAME=ext-wsfeed

include $(CSTBOX_DEVEL_HOME)/lib/makefile-dist.mk

copy_files: \
	copy_python_files \
	copy_etc_files
