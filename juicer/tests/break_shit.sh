#!/bin/bash

# get to top level juicer source directory
function source_dir() {
    SOURCE_DIR=$(pwd | sed -r 's$(.*juicer)(/juicer).*$\1$')
    pushd $SOURCE_DIR > /dev/null
}

# go back to where we were
function go_home() {
    popd > /dev/null
}

# source in hacking/setup-env
function setup() {
    . ./hacking/setup-env > /dev/null
}

# proceed to break shit and display error messages
function break_shit() {
    echo "Create an empty cart..."
    ./bin/juicer create orange -r citrus
    echo -e "\n\n"

    echo "Create a cart with bad rpm..."
    ./bin/juicer create orange -r citrus ~/Downloads/pesticide.rpm
    echo -e "\n\n"

    echo "Show a non-existant cart..."
    ./bin/juicer show orange
    echo -e "\n\n"

    echo "Push a non-existant cart..."
    ./bin/juicer push orange
    echo -e "\n\n"

    echo "RPM search on a non-existant server..."
    ./bin/juicer rpm-search orange.rpm --in florida
    echo -e "\n\n"

    echo "Upload into a non-existant repo"
    ./bin/juicer upload -r citrus ~/Downloads/pesticide.rpm
    echo -e "\n\n"

    echo "Upload into a server"
    ./bin/juicer upload -r citrus ~/Downloads/pesticide.rpm --in florida
    echo -e "\n\n"
}

source_dir
setup
break_shit
go_home
