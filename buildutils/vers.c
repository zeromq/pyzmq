// check libzmq version

#include <stdio.h>
#include "zmq.h"

int main(int argc, char **argv){
    int major, minor, patch;
    zmq_version(&major, &minor, &patch);
    fprintf(stdout, "vers: %d.%d.%d\n", major, minor, patch);
    return 0;
}
