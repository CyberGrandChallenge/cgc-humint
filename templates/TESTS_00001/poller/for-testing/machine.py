from generator.actions import Actions
import random
import string

HI = "Welcome to Palindrome Finder\n"
ASK = "\tPlease enter a possible palindrome: "
YES = "\t\tYes, that's a palindrome!\n"
NO = "\t\tNope, that's not a palindrome\n"

class Palindrome(Actions):
    def start(self):
        pass

    def banner(self):
        # Confirm the actual banner
        self.read(delim='\n', expect=HI)

    def request(self):
        # Confirm the request
        self.read(length=len(ASK), expect=ASK)

    def palindrome(self):
	halfword = self.random_string(random.randint(1, 16))
        self.write(halfword + halfword[::-1] + "\n")
        self.read(delim='\n', expect=YES)

    def not_palindrome(self):
	word = self.random_string(random.randint(2, 32))
	while self.is_palindrome(word):
		word = self.random_string(random.randint(2, 32))
        self.write(word + "\n")
        self.read(delim='\n', expect=NO)

    def is_palindrome(self, word):
	for i in range(0, len(word) / 2):
		if word[i] != word[-i - 1]:
			return False
	return True

    def random_string(self, size):
        chars = string.letters + string.digits
        return ''.join(random.choice(chars) for _ in range(size))
