#include <libcgc.h>

#define BUF_SIZE 128
#define TOKEN_SIZE 4
#define TOKEN_START_PAD "123"
#define TOKEN_START_PAD_LEN 3

#define TOKEN_END_PAD "321"
#define TOKEN_END_PAD_LEN 3

#define TOKEN_BUF_SIZE (TOKEN_START_PAD_LEN + TOKEN_SIZE + TOKEN_END_PAD_LEN)

char* gTokenStart = TOKEN_START_PAD;
char* gTokenEnd = TOKEN_END_PAD;

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
  char token[TOKEN_BUF_SIZE];

  char buf[BUF_SIZE]; 

  int ret = 0;
  int i = 0;
  int j = 0;
  size_t rx_bytes = 0;

  for (i = 0; i < TOKEN_START_PAD_LEN; i++)
  {
    token[i] = gTokenStart[i];
  }

  //doesn't really matter if we don't get all values
  ret = random(token + i, TOKEN_SIZE, NULL);
  if (ret != 0)
  {
    _terminate(0);
  }

  i += TOKEN_SIZE;

  for ( j = 0; j < TOKEN_END_PAD_LEN; j++)
  {
    token[i] = gTokenEnd[j];
    i++;
  }

  transmit_all(token, TOKEN_BUF_SIZE);
 
  receive_all(buf, TOKEN_SIZE);

  for (i = 0; i < TOKEN_SIZE; i++)
  {
    if (token[i + TOKEN_START_PAD_LEN] != buf[i])
    {
      _terminate(0);
    }
  }

#if PATCHED
  j = BUF_SIZE / 2;
#else
  j = BUF_SIZE;
#endif

  ret = receive(STDIN, buf, j, &rx_bytes);
  if ( (ret != 0) || (rx_bytes == 0) )
  {
    _terminate(0);
  }

  for (i = 0; i < rx_bytes; i++)
  {
    buf[rx_bytes + i] = buf[rx_bytes - i - 1];
  }

  transmit_all(buf, rx_bytes * 2);
  return (0);
}
