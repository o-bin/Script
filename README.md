# Script Language Reference                 
## 1. Overview and Execution Model
                                            **Script** is a dynamically typed programming language with optional strict type enforcement within data structures (`struct`). Source files use the `.script` extension.

The reference implementation (`main.py`) operates as a single-file lexer, recursive descent parser, and transpiler that compiles `.script` source code into Python in memory and executes it immediately.

### CLI Usage

```bash
python3 main.py <filename>.script

```

If invoked without arguments or with a file lacking the `.script` extension, the interpreter exits with code `1` and outputs:

```text
usage: python main.py <name_of_your_file>.script

```

---

## 2. Lexical Structure

### 2.1 Comments

Single-line comments start with `//` and extend to the end of the line. Multi-line block comments are not supported.

```rust
// Single-line comment

```

### 2.2 Identifiers

Identifiers start with an ASCII letter (`A-Z`, `a-z`) or underscore (`_`), followed by zero or more letters, digits (`0-9`), or underscores.

### 2.3 Reserved Keywords

The following identifiers are reserved as language keywords:

| Keyword | Category |
| --- | --- |
| `var` | Variable declaration |
| `fn` | Function declaration |
| `struct` | Data structure declaration |
| `if` | Conditional branch |
| `or` | Secondary conditional branch (`else if`) |
| `else` | Fallback conditional branch |
| `while` | Loop control flow |
| `true` | Boolean literal |
| `false` | Boolean literal |
| `return` | Function return and standard output driver |

### 2.4 Reserved Type Identifiers

The following identifiers are reserved exclusively for field type annotations inside `struct` blocks. Using them as standalone expressions or outside a `struct` definition raises a `SyntaxError`:

* `string`
* `integer`
* `float`
* `[]` (Array type token)

---

## 3. Data Types and Literals

| Type | Syntax / Representation | Runtime Behavior |
| --- | --- | --- |
| **Integer** | Sequence of digits (`0`, `42`, `-10`) | 64-bit / arbitrary-precision integer. |
| **Float** | Digits with decimal point (`0.1`, `92.5`) | Double-precision floating-point number. |
| **String** | Double-quoted characters (`"text"`) | Single quotes (`'...'`) are invalid syntax. Supports escape sequences (`\"`, `\n`, `\\`). |
| **Boolean** | `true`, `false` | Evaluates truthiness in conditional and loop expressions. |
| **Array** | `[expr1, expr2, ...]` | Zero-indexed mutable dynamic sequence. Elements may be of any valid type. |

---

## 4. Statements and Declarations

### 4.1 `var` (Variable Declaration)

Declares a mutable variable initialized to an expression. A trailing semicolon (`;`) is mandatory on declarations.

**Syntax:**

```rust
var <identifier> = <expression>;

```

**Reassignment:**
Existing variables, array elements, and struct fields are mutated using the `=` operator without the `var` keyword:

```rust
<target> = <expression>;

```

---

### 4.2 `struct` (Structure Declaration and Instantiation)

Defines a composite data type with strict runtime type checking during instantiation. A trailing semicolon (`;`) after the closing brace `}` is mandatory.

**Declaration Syntax:**

```rust
struct <Identifier> {
    <field_1>: <type>,
    <field_2>: <type>
};

```

Allowed `<type>` specifiers: `string`, `integer`, `float`, `[]`.

**Type Validation Behavior:**

* `string`: Accepts only strings.
* `integer`: Accepts only integers (rejects booleans and floats).
* `float`: Accepts floats and integers (converts integers to float; rejects booleans).
* `[]`: Accepts only array instances.
* Passing a mismatched type at instantiation raises a `TypeError`.

**Instantiation Syntax:**

```rust
var <instance_name> = <StructName> {
    <field_1>: <expression>,
    <field_2>: <expression>
};

```

**Member Access and Mutation:**
Fields are accessed and mutated via the dot (`.`) operator:

```rust
<instance_name>.<field_name>
<instance_name>.<field_name> = <expression>;

```

---

### 4.3 `fn` (Function Declaration)

Declares a callable function accepting zero or more comma-separated parameters. Parameters are dynamically typed and do not take type annotations. Function blocks do not end with a semicolon.

**Syntax:**

```rust
fn <identifier>(<param_1>, <param_2>, ...) {
    <statements>
}

```

**Invocation Syntax:**

```rust
<identifier>(<arg_1>, <arg_2>, ...);

```

---

### 4.4 `if`, `or`, `else` (Conditional Control Flow)

Evaluates conditional branches sequentially. Conditions must be enclosed in parentheses `(...)` and bodies in braces `{...}`.

* `if`: Primary condition.
* `or`: Equivalent to `else if` / `elif`. Zero or more `or` branches may follow an `if` block.
* `else`: Optional fallback block executed if all preceding `if` and `or` conditions evaluate to `false`.

**Syntax:**

```rust
if (<condition_1>) {
    <statements>
} or (<condition_2>) {
    <statements>
} else {
    <statements>
}

```

---

### 4.5 `while` (Iterative Control Flow)

Executes a block of statements repeatedly as long as the condition enclosed in parentheses evaluates to `true`.

**Syntax:**

```rust
while (<condition>) {
    <statements>
}

```

---

### 4.6 `return` (Return and Standard Output Driver)

Acts simultaneously as the function value return mechanism and the sole built-in standard output (`stdout`) driver in the language.

**Syntax:**

```rust
return <expression>;
return;

```

**Behavior:**

1. **Standard Output:** If `<expression>` is provided and does not evaluate to `None`, its formatted representation is printed to `stdout` followed by a newline.
2. **Scope Handling:**
* Inside a `fn` block: Prints the formatted value to `stdout` and terminates the function, returning the raw value to the caller.
* At the top-level (global scope): Prints the formatted value to `stdout` without halting script execution.


3. **Output Formatting Rules:**
* **Primitives (`integer`, `float`, `string`, `boolean`):** Printed as plain values without surrounding quotes.
* **Arrays (`[]`):** Elements are recursively formatted and joined by `, ` without enclosing brackets (`[` `]`) or quotes.
* **Structs:** Each field is printed on a separate line formatted as `<field_name>: <formatted_value>`, without enclosing braces (`{` `}`).



---

## 5. Operators and Expressions

### 5.1 Arithmetic Operators

| Operator | Operation | Associativity / Notes |
| --- | --- | --- |
| `+` | Addition / Concatenation | Binary. Performs numeric addition unless either operand is a `string`, in which case both operands are converted to strings and concatenated. |
| `-` | Subtraction | Binary numeric subtraction. |
| `*` | Multiplication | Binary numeric multiplication. |
| `/` | Division | Binary floating-point division. |
| `-` | Unary Negation | Prefix unary operator (`-x`). |
| `++` | Postfix Increment | Statement-level operator (`x++;`). Increments target by `1`. |
| `--` | Postfix Decrement | Statement-level operator (`x--;`). Decrements target by `1`. |

### 5.2 Relational and Equality Operators

| Operator | Description |
| --- | --- |
| `<` | Less than |
| `<=` | Less than or equal to |
| `>` | Greater than |
| `>=` | Greater than or equal to |
| `==` | Equal to |
| `!=` | Not equal to |

### 5.3 Postfix and Access Operators

| Operator | Syntax | Description |
| --- | --- | --- |
| `()` | `expr(arg1, ...)` | Function call |
| `.` | `expr.identifier` | Struct field access |
| `[]` | `expr[index_expr]` | Zero-based array element access |
| `{}` | `Identifier { k: v }` | Struct literal initialization |

### 5.4 Operator Precedence (Highest to Lowest)

1. Grouping: `( ... )`
2. Postfix operators: `()`, `.`, `[]`, `Struct { ... }`
3. Unary negation: `-x`
4. Multiplicative: `*`, `/`
5. Additive: `+`, `-`
6. Relational and equality: `<`, `<=`, `>`, `>=`, `==`, `!=`
7. Assignment and mutation statements: `=`, `++`, `--`

---

## 6. Formal Grammar Summary (EBNF)

```ebnf
program        = { statement } ;

statement      = var_decl
               | fn_decl
               | struct_decl
               | if_stmt
               | while_stmt
               | return_stmt
               | expr_stmt ;

var_decl       = "var" ID "=" expression ";" ;
fn_decl        = "fn" ID "(" [ param_list ] ")" block ;
param_list     = ID { "," ID } ;

struct_decl    = "struct" ID "{" { field_decl } "}" ";" ;
field_decl     = ID ":" type_spec [ "," ] ;
type_spec      = "string" | "integer" | "float" | "[" "]" ;

if_stmt        = "if" "(" expression ")" block
                 { "or" "(" expression ")" block }
                 [ "else" block ] ;

while_stmt     = "while" "(" expression ")" block ;
return_stmt    = "return" [ expression ] [ ";" ] ;

block          = "{" { statement } "}" ;

expr_stmt      = expression [ ( "=" expression ) | "++" | "--" ] [ ";" ] ;

expression     = comparison ;
comparison     = additive { ( "<" | "<=" | ">" | ">=" | "==" | "!=" ) additive } ;
additive       = multiplicative { ( "+" | "-" ) multiplicative } ;
multiplicative = unary { ( "*" | "/" ) unary } ;
unary          = [ "-" ] postfix ;

postfix        = primary { "(" [ arg_list ] ")"
                         | "." ID
                         | "[" expression "]"
                         | "{" [ struct_init ] "}" } ;

arg_list       = expression { "," expression } ;
struct_init    = field_init { [ "," ] field_init } [ "," ] ;
field_init     = ID ":" expression ;

primary        = INTEGER | FLOAT | STRING | "true" | "false"
               | ID | "(" expression ")" | "[" [ arg_list ] "]" ;
