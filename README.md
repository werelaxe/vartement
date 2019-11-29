## Vartement

Simple functional language. Acronym of **VARiadic TEmplates assignMENT**. Traslation into variadic templates with C++ 17. Program performs in compile-time! Running binary file is only for output operations.

### Support
* Variables
* Assignments
* Functions
* Numeric and functional literals
* Recursion
* Higher-order functions
* Built-in functional lib:
    * Math and logic operations (add, sub, div, or, and, ...)
    * Lists (append, concat, cons, head, map, filter, get)
    * read and print

### Workflow
program.vta -> [input operations via substitutions] -> program.cpp -> program (bin file) -> [output operations via binary file running]

### Example
For running tests: `./run_tests.sh`. Output must be `1\n1\n1\n1\n1\n1\n1\n1`
For translating any file: `translate_and_compile.sh <filename>.vta`
