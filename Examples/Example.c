#define PI 3.14159
#define MAX_BUFFER_SIZE 1024
#define SQUARE(x) ((x) * (x))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define DEBUG 1

#if DEBUG
    printf("Debugging enabled\n");
#else
    printf("Debugging disabled\n");
#endif
#define TO_STRING(x) #x
#define CONCAT(a, b) a ## b
#define LOG(format, ...) printf(format, __VA_ARGS__)
