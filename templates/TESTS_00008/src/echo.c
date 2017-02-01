#include <libcgc.h>
#include "printf.h"

#define BUF_SIZE 128
#define FORMAT_STRING_STR "%s"

int main(void)
{
  char buf[BUF_SIZE];
  size_t rx_bytes;
  int ret = 0;
  
  do
  { 
#ifdef PATCHED
    ret = receive(STDIN, buf, BUF_SIZE - 1, &rx_bytes);
#else
    ret = receive(STDIN, buf, BUF_SIZE * 2, &rx_bytes);
#endif
    
    if ( (ret != 0) || (rx_bytes == 0) )
    {
      return (-1);
    }

    buf[rx_bytes] = '\0';

#ifdef PATCHED
    printf(FORMAT_STRING_STR, buf);
#else
    printf(buf);
#endif
    fflush(STDOUT);

  } while (1);

  return (0);
}
