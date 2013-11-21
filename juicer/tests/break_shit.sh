#!/bin/bash

# helper function to display and run a command
function run() {
    echo $@
    $@
}

# get to top level juicer source directory
function source_dir() {
    SOURCE_DIR=$(pwd | sed -r 's$(.*juicer)(/juicer).*$\1$')
    pushd $SOURCE_DIR > /dev/null
}

# go back to where we were
function go_home() {
    popd > /dev/null

    rm $EMPTY_MANIFEST
}

# source in hacking/setup-env
function setup() {
    CART_FILE=~/.config/juicer/carts/orange.json
    TEST_RPM=./share/juicer/empty-0.0.1-1.fc17.x86_64.rpm
    EMPTY_MANIFEST=./share/juicer/empty.yaml

    if [ -f $CART_FILE ]; then
        rm $CART_FILE
    fi

    . ./hacking/setup-env > /dev/null

    touch $EMPTY_MANIFEST
}

# proceed to break shit and display error messages
function break_shit() {
    echo "Break shit in juicer..."
    echo "Create an empty cart..."
    run ./bin/juicer create orange
    echo -e "\n\n"

    echo "Create a cart with an empty repo..."
    run ./bin/juicer create orange -r citrus
    echo -e "\n\n"

    echo "Create a cart with bad rpm..."
    run ./bin/juicer create orange -r citrus ~/Downloads/pesticide.rpm
    echo -e "\n\n"

    echo "Create a cart from an empty manifest..."
    run ./bin/juicer create orange -f share/juicer/empty.yaml
    echo -e "\n\n"

    echo "Show a non-existant cart..."
    run ./bin/juicer create orange -f share/juicer/nothere.yaml
    echo -e "\n\n"

    echo "Show a non-existant cart..."
    run ./bin/juicer show orange
    echo -e "\n\n"

    echo "Push a non-existant cart..."
    run ./bin/juicer push orange
    echo -e "\n\n"

    echo "Pull a non-existant cart..."
    run ./bin/juicer pull orange
    echo -e "\n\n"

    echo "RPM search on a non-existant server..."
    run ./bin/juicer search orange.rpm --in florida
    echo -e "\n\n"

    echo "Upload into a non-existant repo"
    run ./bin/juicer upload -r citrus $TEST_RPM
    echo -e "\n\n"

    echo "Upload into a non-existant server"
    run ./bin/juicer upload -r citrus $TEST_RPM --in florida
    echo -e "\n\n"

    echo "Break shit in juicer-admin"
    echo "Create a new repo on non-existant server..."
    run ./bin/juicer-admin create-repo citrus --in florida
    echo -e "\n\n"

    echo "Delete a repo on a non-existant server..."
    run ./bin/juicer-admin delete-repo citrus --in florida
    echo -e "\n\n"

    echo "Delete a non-existant repo..."
    run ./bin/juicer-admin delete-repo citrus --in qa
    echo -e "\n\n"

    echo "Create a user on a non-existant server..."
    run ./bin/juicer-admin create-user plantman --name citrus --password sinensis --in florida
    echo -e "\n\n"

    echo "Create a duplicate user..."
    ./bin/juicer-admin create-user plantman > /dev/null
    run ./bin/juicer-admin create-user plantman
    echo -e "\n\n"

    echo "List roles for non-existant server..."
    run ./bin/juicer-admin list-roles --in florida
    echo -e "\n\n"

    echo "Add non-existant role to user..."
    run ./bin/juicer-admin role-add --login plantman --role zombie
    echo -e "\n\n"

    echo "Add role to non-existant user..."
    run ./bin/juicer-admin role-add --login mechanicalman --role super-users
    echo -e "\n\n"

    echo "Update a user on a non-existant server..."
    run ./bin/juicer-admin update-user --name citrus --password sinensis plantman --in florida
    echo -e "\n\n"
    
    echo "Update a non-existant user..."
    run ./bin/juicer-admin update-user --name citrus --password sinensis mechanicalman
    echo -e "\n\n"

    echo "Show user on non-existant server..."
    run ./bin/juicer-admin show-user plantman --in florida
    echo -e "\n\n"
    
    echo "Show non-existant user..."
    run ./bin/juicer-admin show-user mechanicalman
    echo -e "\n\n"
    
    echo "Delete a user on a non-existant server..."
    run ./bin/juicer-admin delete-user plantman --in florida
    echo -e "\n\n"

    echo "Delete a non-existant user..."
    # take this opportunity to clean up from earlier
    ./bin/juicer-admin delete-user plantman > /dev/null
    run ./bin/juicer-admin delete-user plantman
    echo -e "\n\n"
    
    echo "List repos on a non-existant server..."
    run ./bin/juicer-admin list-repos --in florida
    echo -e "\n\n"

    echo "Show repo on non-existant server..."
    run ./bin/juicer-admin show-repo citrus --in florida
    echo -e "\n\n"

    echo "Show non-existant repo..."
    run ./bin/juicer-admin show-repo citrus
}

source_dir
setup
break_shit
go_home
