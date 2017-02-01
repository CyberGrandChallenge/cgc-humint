//CADET's first C program

#include <libcgc.h>
#include "libc.h"

#define HI "Welcome to Palindrome Finder\n"
#define ASK "\tPlease enter a possible palindrome: "
#define YES "\t\tYes, that's a palindrome!\n"
#define NO "\t\tNope, that's not a palindrome\n"
#define EASTEREGG "\n\nEASTER EGG!\n\n"

#define BUF_SIZE 64

int check();

int main(void) {
    int r;

    transmit_all(1, HI, sizeof(HI)-1);
    
    while(1){
        transmit_all(1, ASK, sizeof(ASK)-1);
        r = check();
        if (r == -1){
            break;
        }
        else if (r == 0){
            transmit_all(1, NO, sizeof(NO)-1);
        }
        else{
            transmit_all(1, YES, sizeof(YES)-1);
        }
    }
    return 0;
}

int check(){
    int len = -1;
    int i;
    int pal = 1;
    char string[BUF_SIZE];
    size_t letter;
    for (i = 0; i < sizeof(string); i++)
        string[i] = '\0';
#ifdef PATCHED
    if (receive(0, string, sizeof(string), &letter) || letter == 0)
        return -1;
#else    
    if (receive(0, string, BUF_SIZE*2, &letter) || letter == 0)
        return -1;
#endif
    for(i = 0; string[i] != '\0'; i++){
        len++;
    }
    int steps = len;
    if(len % 2 == 1){
        steps--;
    }
    for(i = 0; i <= steps/2; i++){
        if(string[i] != string[len-1-i]){
            pal = 0;
        }
    }
    if(string[0] == '^'){
        transmit_all(1, EASTEREGG, sizeof(EASTEREGG)-1);
    }    
    return pal;
}
