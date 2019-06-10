#!/bin/bash
(echo 'package gosai'
echo '// #cgo CFLAGS: -I../../SAI/inc'
echo '//#include "sai.h"'
echo 'import "C"'
echo
echo 'const ('
echo '#include "SAI/inc/sai.h"' |
     gcc -x c - -E -dD  -I SAI/inc |
     grep 'define SAI_[^ \(]*[ ]' |
     awk -v q=\" 'BEGIN{print "#include " q "SAI/inc/sai.h" q} {print q $2 q " = "$2}' |
     gcc -x c - -E   -I SAI/inc |
     sed -e '1,/# 2 "<stdin>" 2/d' |
     tr -d '"()' |
     sed -E 's/ = ([x0-9a-fA-F]*)$/ = \1/' |
     sed -E 's/ = (.*)L$/ = \1/' |
     sed -E 's/ = (SAI.*)$/ = "\1"/' |
     sed -E 's/PATH_MAX/4096/'
echo ')'
)> goSAIadapterBuilder/adaptor/gosai/saidefinesgen.go