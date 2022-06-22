import sys
from lex import *

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer

        self.symbols = set() # Variables declared so far
        self.labelsDeclared = set() # Labels declared so far
        self.labelGotoed = set() # label goto'ed so far

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken() # called twice to initialize current and peek

    # return true if the current token matches
    def checkToken(self, kind):
        return kind == self.curToken.kind

    # return true if the next token matches
    def checkPeek(self, kind):
        return kind == self.peekToken.kind

    # Try to match the current token. If not, error. Advances current token
    def match(self, kind):
        if not self.checkToken(kind):
            self.abort("Expected " + kind.name + ", got " + self.curToken.kind.name)
        self.nextToken()

    # Advances the current token
    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()
        # no need to worry about parsing EOF, lexer handles that

    def abort(self, message):
        sys.exit("Error. " + message)

    # Production rules

    # program ::= {statement}
    def program(self):
        print("PROGRAM")

        # Skip newline at the beginning
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

        # Parse all the statements in the program
        while not self.checkToken(TokenType.EOF):
            self.statement()

        # Check that each label referenced in a GOTO is declared
        for label in self.labelGotoed:
            if label not in self.labelsDeclared:
                self.abort("Attempting to GOTO to undeclared label: " + label)

    # one of the statement(s)
    def statement(self):
        # Check the first token

        # "PRINT" (expression | string)
        if self.checkToken(TokenType.PRINT):
            print("STATEMENT-PRINT")
            self.nextToken()

            if self.checkToken(TokenType.STRING):
                # string
                self.nextToken()
            else:
                # expression
                self.expression()

        # "IF" comparison "THEN" {statement} "ENDIF"
        elif self.checkToken(TokenType.IF):
            print("STATEMENT-IF")
            self.nextToken()
            self.comparison()

            self.match(TokenType.THEN)
            self.nl()

            # zero or more statements in the body
            while not self.checkToken(TokenType.ENDIF):
                self.statement()

            self.match (TokenType.ENDIF)

        # "WHILE" comparison "REPEAT" {statement} "ENDWHILE"
        elif self.checkToken(TokenType.WHILE):
            print("STATEMENT-WHILE")
            self.nextToken()
            self.comparison()

            self.match(TokenType.REPEAT)
            self.nl()

            # Zero or more statements in the loop body
            while not self.checkToken(TokenType.ENDWHILE):
                self.statement()

            self.match(TokenType.ENDWHILE)

        # "LABEL" ident
        elif self.checkToken(TokenType.LABEL):
            print("STATEMENT-LABEL")
            self.nextToken()

            if self.curToken.text in self.labelsDeclared:
                self.abort("Label already exists: " + self.curToken.text)
            self.labelsDeclared.add(self.curToken.text)

            self.match(TokenType.IDENT)

        # "GOTO" ident
        elif self.checkToken(TokenType.GOTO):
            print("STATEMENT-GOTO")
            self.nextToken()
            self.labelGotoed.add(self.curToken.text)
            self.match(TokenType.IDENT)

        # "LET" ident "=" expression
        elif self.checkToken(TokenType.LET):
            print("STATEMENT-LET")
            self.nextToken()

            # Check if ident exists in symbols table, if not then declare it
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)

            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)

            self.expression()

        # "INPUT" ident
        elif self.checkToken(TokenType.INPUT):
            print("STATEMENT-INPUT")
            self.nextToken()

            # If varables doesn't already exist, declare it
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)

            self.match(TokenType.IDENT)

        else:
            self.abort("Invalid statement at " + self.curToken.text + " (" + self.curToken.kind.name + ")")

        # newline
        self.nl()

    # comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+
    def comparison(self):
        print("COMPARISON")

        self.expression()
        if self.isComparisonOperator():
            self.nextToken()
            self.expression()
        else:
            self.abort("Expected comparison operator at: " + self.curToken.text)

        while self.isComparisonOperator():
            self.nextToken()
            self.expression()

    # return true if token is comparison operator
    def isComparisonOperator(self):
        return self.checkToken(TokenType.GT)\
                or self.checkToken(TokenType.GTEQ)\
                or self.checkToken(TokenType.LT)\
                or self.checkToken(TokenType.LTEQ)\
                or self.checkToken(TokenType.EQEQ)\
                or self.checkToken(TokenType.NOTEQ)\

    # expression ::= term{( "-" | "+" ) term}
    def expression(self):
        print("EXPRESSION")

        self.term()
        # Can have 0 or more +\- and expressions
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.nextToken()
            self.term()

    # term ::= unary {( "/" | "*" ) unary}
    def term(self):
        print("TERM")

        self.unary()
        # Can have 0 or more *// expressions
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            self.nextToken()
            self.unary()

    # unary ::= ["+" | "-"] primary
    def unary(self):
        print("UNARY")

        # Optional unary
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.nextToken()
        self.primary()

    # primary ::= number | ident
    def primary(self):
        print("PRIMARY (" + self.curToken.text + ")")

        if self.checkToken(TokenType.NUMBER):
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            if self.curToken.text not in self.symbols:
                self.abort("Referencing variable before assignment: " + self.curToken.text)
            self.nextToken()
        else:
            # Error
            self.abort("Unexpected token at " + self.curToken.text)

    # nl :: = '\n'+
    def nl(self):
        print("NEWLINE")

        # require at least one newline
        self.match(TokenType.NEWLINE)
        # but extra newlines are allow
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()
