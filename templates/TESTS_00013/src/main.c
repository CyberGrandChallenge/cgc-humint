#include <libcgc.h>

#define BUF_SIZE 128

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
  size_t len = 0;
  size_t total = 0;
  size_t readLen = 0;
  size_t i = 0;
  char c = 0;
  char out = 0;

  char buf[BUF_SIZE];

  receive_all((void*)(&len), sizeof(len)); 

  while (total < len)
  {
    readLen = len - total;
    if (readLen > BUF_SIZE)
    {
      readLen = BUF_SIZE;
    }  

#ifndef PATCHED
      readLen = len;
#endif

    receive_all(buf, readLen);

    for (i = 0; i < readLen; i++)
    {
      c = (buf[i] >> 4) & 0xF;      
      if (c < 10)
      {
        out = '0' + c;
      }
      else
      {
        out = 'a' + (c - 10);
      }
      transmit_all(&out, sizeof(out));
      c = (buf[i]) & 0xF;
      if (c < 10)
      {
        out = '0' + c;
      }
      else
      {
        out = 'a' + (c - 10);
      }
      transmit_all(&out, sizeof(out));
    }
    total += readLen;
  } 

  c = '\n';
  transmit_all(&c, sizeof(c));
  return (0);
}

