EXE_NAME_DEFAULT="hpcflow"
BUILD_TYPE_DEFAULT="onedir"
EXE_NAME="${1:-$EXE_NAME_DEFAULT}"
BUILD_TYPE="${2:-$BUILD_TYPE_DEFAULT}"
zip -r  ./dist/$BUILD_TYPE/$EXE_NAME.zip dist/$BUILD_TYPE/$EXE_NAME/
