#include <libcgc.h>

#define MAX_SIZE (4096 * 4)

void receive_all(void* buf, size_t size)
{
  size_t rx_bytes = 0;
  int ret = 0;
  size_t total = 0;
 
  do
  {
    ret = receive(STDIN, buf + total, size - total, &rx_bytes);
    if ( (ret != 0) || (rx_bytes == 0) )
    {
      _terminate(ret);
    }
    total += rx_bytes;
  } while (total < size);
}

void transmit_all(void* buf, size_t size)
{
  size_t rx_bytes = 0;
  int ret = 0;
  size_t total = 0;
 
  do
  {
    ret = transmit(STDOUT, buf + total, size - total, &rx_bytes);
    if ( (ret != 0) )
    {
      _terminate(ret);
    }
    total += rx_bytes;
  } while (total < size);
}

int main(void)
{
#ifdef PATCHED
  size_t len = 0;
#else
  int len = 0;
#endif
  size_t i = 0;
  char c = 0;
  char out = 0;
  int ret = 0;

  char* buf = NULL;
  size_t tempTotal = 0;
  size_t total = 0;

  receive_all((void*)(&len), sizeof(len)); 
  //needs to be an even number
  if ( (len == 0) || (len % 2) )
  {
    return (0);
  }

  //There is a signed-unsigned mismatch here
  if (len < MAX_SIZE) 
  {
    ret = allocate(len, 0, (void**)(&buf));  
  }
  else
  {
    return (0);
  }

#ifdef PATCHED
  if (ret != 0)
  {
    _terminate(1);
  }
#endif

  //There is a signed-unsigned mismatch here as well
  for (i = 0; i < len; i++) 
  {
    buf[i] = 0;
  } 

  receive_all(buf, len);
  for (i = 0; i < len; i+=2)
  {
    out = 0;

    if ( (buf[i] >= '0') && (buf[i] <= '9') )
    {
      out = (buf[i] - '0') & 0xF;
    }
    else if ( (buf[i] >= 'a') && (buf[i] <= 'f') )
    {
      out = 10 + ((buf[i] - 'a') & 0xF);
    }
    else if ( (buf[i] >= 'A') && (buf[i] <= 'F') )
    {
      out = 10 + ((buf[i] - 'A') & 0xF);
    }
    else
    {
      return (0);
    }
    out = out << 4;

    if ( (buf[i+1] >= '0') && (buf[i+1] <= '9') )
    {
      out |= (buf[i+1] - '0') & 0xF;
    }
    else if ( (buf[i+1] >= 'a') && (buf[i+1] <= 'f') )
    {
      out |= 10 + ((buf[i+1] - 'a') & 0xF);
    }
    else if ( (buf[i+1] >= 'A') && (buf[i+1] <= 'F') )
    {
      out |= 10 + ((buf[i+1] - 'A') & 0xF);
    }
    else
    {
      return (0);
    }

    transmit_all(&out, sizeof(out));
  }

  return (0);
}

