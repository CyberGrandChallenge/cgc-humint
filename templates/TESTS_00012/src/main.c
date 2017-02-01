#include <libcgc.h>

typedef unsigned int uint32_t;

#define END_INSN (0xFFFFFFFF)
#define INSN_TO_OPCODE(_x) (_x & 0xFF)
#define INSN_TO_IMM(_x) (_x >> 8)
#define PUSH (0x0)
#define POP (0x1)
#define PUSHPC (0x2)
#define JMPZ (0x3)
#define SWAP (0x4)
#define DUP (0x5)
#define ADD (0x6)
#define SUB (0x7)

#define _MAX_STACK_SIZE_IN_BYTES_ (4096)
#define _MAX_INSNS_SIZE_IN_BYTES_ (8192)
#define _MAX_STACK_SIZE_ (_MAX_STACK_SIZE_IN_BYTES_/4)
#define _MAX_INSNS_SIZE_ (_MAX_INSNS_SIZE_IN_BYTES_/4)

#define _STACK_OVERFLOW_EXCP_MSG_ "SOE\n"
#define _STACK_UNDERFLOW_EXCP_MSG_ "SUE\n"
#define _INSNS_OVERFLOW_EXCP_MSG_ "IOE\n"
#define _ILLEGAL_INSN_EXCP_MSG_ "IIE\n"
#define _PC_EXCP_MSG_ "IPE\n"

size_t transmit_all(char* buf, size_t size)
{
  size_t rx_bytes = 0;
  size_t total = 0;
  int ret = 0;
  if (buf == NULL)
  {
    return (0);
  }
  
  do
  {
    ret = transmit(STDOUT, buf, size - total, &rx_bytes);
    if ( (ret != 0) || (rx_bytes == 0) )
    {
      _terminate(1);
    }
    total += rx_bytes;
  }
  while (total < size);

  return (size);
}

//char gHelpMsg[] = "";

#ifdef DEBUG
void debugPrintDecimal(uint32_t num)
{
  int i = 0;
  int j = 0;
  uint32_t rem = 0;
  char temp[24]; //the maximum uint64_t value is 2^64 - 1
                 // which is approx 10^20 so 24 characters should be good
  char temp2[24];

  temp[0] = '0';
  temp[1] = '\0';

  if (num == 0)
  {
    i = 1;
  }
  else 
  {
    while (num != 0)
    {
      rem = num % 10; //get the remainder
      temp2[i] = '0' + rem;
      num = num / 10; //divide it by 10 
      i++;
    }
    for (j = i - 1; j >= 0; j--)
    {
      temp[(i-1)-j] = temp2[j];
    } 
  }

  transmit(STDERR, temp, i, NULL);
}
#endif

int main(void)
{
  uint32_t insn = 0;
  size_t rx_bytes = 0;
  size_t total = 0;
  int curTop = -1;
  int totalInsns = 0;
  int pc = 0;
  int ret = 0;

  uint32_t* insns = NULL;
  uint32_t* stack = NULL;

  void* b1 = NULL;
  void* b2 = NULL;
  allocate(_MAX_STACK_SIZE_IN_BYTES_, 0, &b1);
  allocate(_MAX_STACK_SIZE_IN_BYTES_, 0, (void**)(&stack));
  allocate(_MAX_STACK_SIZE_IN_BYTES_, 0, &b2);
  allocate(_MAX_INSNS_SIZE_IN_BYTES_, 0, (void**)(&insns));

  deallocate(b1, _MAX_STACK_SIZE_IN_BYTES_);
  deallocate(b2, _MAX_STACK_SIZE_IN_BYTES_);

  do
  {
    total = 0;
    do
    {
      ret = receive(STDIN, ((char*)(&insn)) + total, sizeof(insn) - total, &rx_bytes);
      if ( (ret != 0) || (rx_bytes == 0) )
      {
        if (totalInsns == 0)
        {
          //transmit_all(gHelpMsg, sizeof(gHelpMsg));
        }
        _terminate(-1);
      }
      total += rx_bytes;
    } while (total < sizeof(insn));

    insns[totalInsns] = insn;
    totalInsns++;
    if (totalInsns >= _MAX_INSNS_SIZE_)
    {
      transmit_all(_INSNS_OVERFLOW_EXCP_MSG_, sizeof(_INSNS_OVERFLOW_EXCP_MSG_));
      _terminate(-1);
    }
  } while (insn != END_INSN);


  for (pc = 0; (pc < totalInsns) && (insns[pc] != END_INSN) ; pc++)
  {
    insn = insns[pc];
    if (insn == END_INSN)
    {
      break;
    }

#ifdef DEBUG
    debugPrintDecimal(pc);
#endif

    switch (INSN_TO_OPCODE(insn))
    {
      case (PUSH):
      {
#ifdef DEBUG
        transmit(STDERR, ": push ", 7, NULL);
#endif
        curTop++;
#ifdef PATCHED
        if (curTop >= _MAX_STACK_SIZE_)
        {
          transmit_all(_STACK_OVERFLOW_EXCP_MSG_, sizeof(_STACK_OVERFLOW_EXCP_MSG_));
          _terminate(-1);
        }
#endif
        stack[curTop] = INSN_TO_IMM(insn);
#ifdef DEBUG
        debugPrintDecimal(INSN_TO_IMM(insn));
        transmit(STDERR, "\n", 1, NULL);
#endif 
        break;
      }
      case (POP):
      {
#ifdef DEBUG
        transmit(STDERR, ": pop\n", 6, NULL);
#endif
        if (curTop < 0)
        {
          transmit_all(_STACK_UNDERFLOW_EXCP_MSG_, sizeof(_STACK_UNDERFLOW_EXCP_MSG_));
          _terminate(-1);
        }
        curTop--;
        break;
      }
      case (PUSHPC):
      {
#ifdef DEBUG
        transmit(STDERR, ": pushpc\n", 9, NULL);
#endif
        curTop++;
        if (curTop >= _MAX_STACK_SIZE_)
        {
          transmit_all(_STACK_OVERFLOW_EXCP_MSG_, sizeof(_STACK_OVERFLOW_EXCP_MSG_));
          _terminate(-1);
        }
        stack[curTop] = pc;
        break;
      }
      case (JMPZ):
      { 
#ifdef DEBUG
        transmit(STDERR, ": jmpz\n", 7, NULL);
#endif
        if (curTop < 1)
        {
          transmit_all(_STACK_UNDERFLOW_EXCP_MSG_, sizeof(_STACK_UNDERFLOW_EXCP_MSG_));
          _terminate(-1);
        }

        if (stack[curTop] == 0)
        {
          pc = stack[curTop - 1];
          if ((pc < 0) || (pc >= totalInsns))
          {
            transmit_all(_PC_EXCP_MSG_, sizeof(_PC_EXCP_MSG_));
            _terminate(-1);
          }
          pc--; //for the pc++ at the end of the loop
        }
        curTop -= 2;
        break;
      }
      case (SWAP):
      {
#ifdef DEBUG
        transmit(STDERR, ": swap ", 7, NULL);
#endif
        if (curTop < 0)
        {
          transmit_all(_STACK_UNDERFLOW_EXCP_MSG_, sizeof(_STACK_UNDERFLOW_EXCP_MSG_));
          _terminate(-1);
        }

        uint32_t temp = stack[curTop];
        int temp2 = curTop - INSN_TO_IMM(insn);
        
#ifdef DEBUG
        debugPrintDecimal(INSN_TO_IMM(insn));
        transmit(STDERR, "\n", 1, NULL);
#endif
        if ( (temp2 < 0) || (temp2 > curTop) )
        {
          transmit_all(_STACK_UNDERFLOW_EXCP_MSG_, sizeof(_STACK_UNDERFLOW_EXCP_MSG_));
          _terminate(-1);
        }

        stack[curTop] = stack[temp2];
        stack[temp2] = temp;

        break;
      } 
      case (DUP):
      {
#ifdef DEBUG
        transmit(STDERR, ": dup ", 6, NULL);
#endif
        curTop++;
#ifdef PATCHED
        if (curTop >= _MAX_STACK_SIZE_)
        {
          transmit_all(_STACK_OVERFLOW_EXCP_MSG_, sizeof(_STACK_OVERFLOW_EXCP_MSG_));
          _terminate(-1);
        }
#endif
        int temp = curTop - INSN_TO_IMM(insn) - 1;

#ifdef DEBUG
        debugPrintDecimal(INSN_TO_IMM(insn));
        transmit(STDERR, "\n", 1, NULL);
#endif

        if ( (temp < 0) || (temp > curTop) )
        {
          transmit_all(_STACK_UNDERFLOW_EXCP_MSG_, sizeof(_STACK_UNDERFLOW_EXCP_MSG_));
          _terminate(-1);
        }

        stack[curTop] = stack[curTop - INSN_TO_IMM(insn) - 1];
        break;
      }
      case (ADD):
      {
#ifdef DEBUG
        transmit(STDERR, ": add\n", 6, NULL);
#endif
        if (curTop < 1)
        {
          transmit_all(_STACK_UNDERFLOW_EXCP_MSG_, sizeof(_STACK_UNDERFLOW_EXCP_MSG_));
          _terminate(-1);
        }
        stack[curTop - 1] += stack[curTop];
        curTop--;  
        break;
      }
      case (SUB):
      {
#ifdef DEBUG
        transmit(STDERR, ": sub\n", 6, NULL);
#endif
        if (curTop < 1)
        {
          transmit_all(_STACK_UNDERFLOW_EXCP_MSG_, sizeof(_STACK_UNDERFLOW_EXCP_MSG_));
          _terminate(-1);
        }
        stack[curTop - 1] -= stack[curTop];
        curTop--;  
        break;
      }
      default :
      {
        //empty
      }
    }
  }

  if (curTop < 0)
  {
    transmit_all(_STACK_UNDERFLOW_EXCP_MSG_, sizeof(_STACK_UNDERFLOW_EXCP_MSG_));
    _terminate(-1);
  }

  transmit_all(&stack[curTop], sizeof(uint32_t));

  return (0);
}

