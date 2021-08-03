#include <stdio.h>
#if defined _MSC_VER
#include <afunix.h>
#else
#include <sys/un.h>
#endif

int main(int argc, char **argv) {
    struct sockaddr_un *dummy;
    printf("%lu\n", sizeof(dummy->sun_path) - 1);
    return 0;
}
