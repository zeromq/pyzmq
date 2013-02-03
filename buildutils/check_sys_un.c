#include <stdio.h>
#include "sys/un.h"

int main(int argc, char **argv) {
    struct sockaddr_un *dummy;
    printf("%lu\n", sizeof(dummy->sun_path) - 1);
    return 0;
}
